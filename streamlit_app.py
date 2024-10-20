from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from chat_agent import ChatAgent
from cgm import CGM
import pandas as pd
import numpy as np
import altair as alt
import time
import vectara_client as vectara
from decimal import Decimal, ROUND_DOWN


import streamlit as st

st.set_page_config(page_title="Prime agent: Chat with search", page_icon="P")
st.title("Chat with agent")

openai_api_key = st.secrets["OpenAI_key"]

# openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)
# if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
if len(msgs.messages) == 0:
    msgs.clear()
    msgs.add_ai_message("Do you want to check on this selection")
    st.session_state.steps = {}


# -------- activity widget ------------------
HYPER_GLY = 120
NORMAL_GLY = 85
HYPO_GLY = 70
DANGER_GLY = 60

# Initialize session state for the selected option
if "selected_option_activity" not in st.session_state:
    st.session_state.selected_option_activity = "Select an option..."
if "formatted_activity_prompt" not in st.session_state:
    st.session_state.formatted_activity_prompt = None
if "formatted_activity_prompt_gl_sn2" not in st.session_state:
    st.session_state.formatted_activity_prompt_gl_sn2 = None
if "formatted_activity_prompt_gl_sn1" not in st.session_state:
    st.session_state.formatted_activity_prompt_gl_sn1 = None
if "formatted_activity_prompt_normal" not in st.session_state:
    st.session_state.formatted_activity_prompt_normal = None
if "glucose_chart_session" not in st.session_state:
    cgm = CGM(start_time = pd.Timestamp.now(), num_points=1, duration_in_minutes=5)
    st.session_state.glucose_chart_session = cgm.initiate_cgm_chart()
if "time_session" not in st.session_state:
    st.session_state.time_session = pd.Timestamp.now()
# if "new_glucose_level" not in st.session_state:
#     st.session_state.new_glucose_level = NORMAL_GLY
if "low_glucose_level" not in st.session_state:
    st.session_state.low_glucose_level = None
if "cgm_user_msg" not in st.session_state:
    st.session_state.cgm_user_msg = None
if "cgm_user_msg1" not in st.session_state:
    st.session_state.cgm_user_msg1 = None
if "cgm_user_normal_msg" not in st.session_state:
    st.session_state.cgm_user_normal_msg = None

if "emergency_step" not in st.session_state:
    st.session_state.emergency_step = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

if "launch_cgm" not in st.session_state:
    st.session_state.launch_cgm = None


if "selected_option_meal" not in st.session_state:
    st.session_state.selected_option_meal = "Select an option..."
if "formatted_meal_prompt" not in st.session_state:
    st.session_state.formatted_meal_prompt = None


# --- gl text box ---
if "txt_gl" not in st.session_state:
    st.session_state.txt_gl = None


def update_selection():
    st.session_state.selected_option_activity = st.session_state.key_activity

    prompt_template = PromptTemplate(
        input_variables=["activity"],
        template="Do you want to check this {activity} activity impact your current glucose level?"
    )
    st.write(f"Ask more to agent on : {st.session_state.selected_option_activity}")
    # st.write(f"selected the key_activity: {st.session_state.key_activity}")
     # ---- activity prompt ----/
    formatted_activity_prompt = prompt_template.format(activity=st.session_state.selected_option_activity)
    #------------------------
    # memory.chat_memory.add_user_message(formatted_activity_prompt)
    memory.chat_memory.add_user_message(formatted_activity_prompt)
    st.session_state.formatted_activity_prompt = formatted_activity_prompt



@st.fragment
def frg_option(key = "key_activity"):
    selected_option = st.selectbox(
        "Select an Exercise and chat with agent:", 
        ['Select an option...','Cardio', 'Weight', 'Swimming'], 
        key="key_activity",
        on_change=update_selection    
        )   
        # Display the selected option from session state
    if st.session_state.selected_option_activity:
        st.write(f"You selected: {st.session_state.selected_option_activity}")


def update_selection_meal():
    st.session_state.selected_option_meal = st.session_state.key_meal

    prompt_template_meal = PromptTemplate(
        input_variables=["meal", "report"],
        template="Check {meal} with your report {report} and suggest a meal plan?"
    )

    # ---- search management report --------
    report_result = "Meal"
    result = vectara.query_vectara_diabetes_plan("What it says about meal plan?")
    responses = result.get('responseSet', [])
    if responses:
        for i, response in enumerate(responses[0].get('response', []), 1):
            print(f"\n{i}. {response.get('text')}")
            report_result = response.get('text')
            # st.write(report_result)
            break
    else:
        print("No meals results found.")
    # ----
     # ---- activity prompt ----/
    formatted_meal_prompt = prompt_template_meal.format(meal=st.session_state.selected_option_meal, report=report_result)
    #------------------------
    # memory.chat_memory.add_user_message(formatted_activity_prompt)
    memory.chat_memory.add_ai_message(formatted_meal_prompt)
    st.session_state.formatted_meal_prompt = formatted_meal_prompt

@st.fragment
def frg_meal(key = "key_meal"):
    selected_option = st.selectbox(
        "Select a meal plan and chat with agent:", 
        ['Select an option...','Rice', 'Fruits', 'Salads'], 
        key="key_meal",
        on_change=update_selection_meal  
        )   
        # Display the selected option from session state
    if st.session_state.selected_option_meal:
        st.write(f"You selected: {st.session_state.selected_option_meal}")

@st.fragment
def frg_display_activity():
    selected_value = st.session_state["key_activity"]
    st.write(f"Value from the fragment (accessed outside): {selected_value}")

# -----------------------activity widget ends --------------------------


# ---------------------- CGM widget -----------------------------------

# def insert_cgm_message_agent(new_gl_level):
#     st.write(f"Inside cgm message {new_gl_level}")
#     user_message = "glucose level going below 70 at :" + str(new_gl_level)
#     if user_message:
#         msgs.add_ai_message(user_message)

#         prompt_template_low_gly_sn2 = PromptTemplate(
#         input_variables=["low_gly_user_input_sn2"],
#         template="Want other suggestions for fast acting carbohydrates for {low_gly_user_input_sn2} "
#         )
#         st.write(f"Say yes to agent for help...")
#         # ---- prompt_template_low_gly_sn2 prompt ----/
#         formatted_activity_prompt_gl_sn2 = prompt_template_low_gly_sn2.format(low_gly_user_input_sn2= user_message)
#         #------------------------
#         # memory.chat_memory.add_user_message(formatted_activity_prompt)
#         memory.chat_memory.add_user_message(formatted_activity_prompt_gl_sn2)
#         st.session_state.formatted_activity_prompt_gl_sn2 = formatted_activity_prompt_gl_sn2

def update_gl_text():
    st.session_state.txt_gl = st.session_state.key_gl

    #------- glucose level above 70 normals ----
    new_glucose_level = st.session_state.key_gl
    if Decimal(new_glucose_level) > 70:   
        user_message = "Check blood sugar level going at :" + str(new_glucose_level) + "mg/dL"       
        report_result = "Is this a normal range?"
        if st.session_state.txt_gl is None:    
            st.session_state.txt_gl = user_message;  
                # -- call corpus 
            result = vectara.query_vectara("What it says about normal glucose level?")
            responses = result.get('responseSet', [])
            if responses:
                for i, response in enumerate(responses[0].get('response', []), 1):
                    print(f"\n{i}. {response.get('text')}")
                    report_result = response.get('text')
                    st.write(report_result)
                    break
            else:
                print("No results found.")
            st.write(user_message)
        

        if user_message:
            msgs.add_ai_message(user_message)
            # Sample input values
            inputs = {
                "report_result": report_result,
                "normal_gly": user_message
            }
            prompt_template_normal = PromptTemplate(
                input_variables=["report_result", "normal_gly"],
                # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
                template="Given my report: ""{report_result}"" do you want to check impact on my levels at {normal_gly} ?"

            )
            
            # ---- prompt_template_low_gly_sn1 prompt ----/
            formatted_activity_prompt_normal = prompt_template_normal.format(**inputs)
            #------------------------
            # memory.chat_memory.add_user_message(formatted_activity_prompt)
            memory.chat_memory.add_user_message(formatted_activity_prompt_normal)
            st.session_state.formatted_activity_prompt_normal = formatted_activity_prompt_normal
        return

        #------- glucose level hypo ----

    if Decimal(new_glucose_level) <= 70 and Decimal(new_glucose_level) >= 55:  
        user_message = "Your blood sugar level is low " + str(new_glucose_level) + "mg/dL" + ". Have a sugary snack or drink 6 oz of fruit juice. Do you want other suggestions for fast acting carbohydrates?"
        if st.session_state.txt_gl is None:    
            st.session_state.txt_gl = user_message;  
        
        if user_message:
            msgs.add_user_message(user_message)
            prompt_template_low_gly_sn2 = PromptTemplate(
                input_variables=["low_gly_user_input_sn1"],
                # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
                template="Check blood sugar level info for {low_gly_user_input_sn1} mg/dL ...."

            )
            
            # ---- prompt_template_low_gly_sn1 prompt ----/
            formatted_activity_prompt_gl_sn2 = prompt_template_low_gly_sn2.format(low_gly_user_input_sn1 = new_glucose_level)
            #------------------------
            # memory.chat_memory.add_user_message(formatted_activity_prompt)
            memory.chat_memory.add_user_message(formatted_activity_prompt_gl_sn2)
            memory.chat_memory.add_ai_message("Regular mealtimes keep your blood sugar levels in range. Do you want help with making healthy food choices?")           
            st.session_state.formatted_activity_prompt_gl_sn2 = formatted_activity_prompt_gl_sn2
        return

        #-------------------------------

         #------- glucose level hypo scenario 2 ----

    if Decimal(new_glucose_level) < 55:  
        user_message = "Your blood sugar level is dangerously low. The emergency glucagon kit is located in my bag. Here are the instructions on how to administer glucagon."
        if st.session_state.txt_gl is None:    
            st.session_state.txt_gl = user_message;  
        
        if user_message:
            msgs.add_user_message("Emergency alert")
            msgs.add_user_message(user_message)
            prompt_template_low_gly_sn1 = PromptTemplate(
                input_variables=["low_gly_user_input_sn1"],
                # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
                template="Agent pulls up info on glucagon administration from peer reviewed source {low_gly_user_input_sn1} ?"

            )
            
            # ---- prompt_template_low_gly_sn1 prompt ----/
            formatted_activity_prompt_gl_sn1 = prompt_template_low_gly_sn1.format(low_gly_user_input_sn1 = new_glucose_level)
            #------------------------
            # memory.chat_memory.add_user_message(formatted_activity_prompt)
            memory.chat_memory.add_user_message(formatted_activity_prompt_gl_sn1)
            st.session_state.formatted_activity_prompt_gl_sn1 = formatted_activity_prompt_gl_sn1
        return
        #-------------------------------
        # frg_emergency()

@st.fragment()
def frg_cgm_text_update():
        
        sugar_ip = st.text_input("Enter blood sugar reading:", on_change=update_gl_text, key="key_gl")
        # new_glucose_level_rounded = decimal_gl_txt.quantize(Decimal('0.0'), rounding=ROUND_DOWN)
        

def update_ins_text():
    st.session_state.txt_ins = st.session_state.key_ins

    #------- glucose level above 70 normals ----
    new_glucose_level = st.session_state.key_ins
    if new_glucose_level:   
        user_message = "Check for carbohydrate content :" + str(new_glucose_level) +"grams"   
        if st.session_state.txt_ins is None:    
            st.session_state.txt_ins = user_message;  
                # -- call corpus 
        if user_message:
            prompt_template = PromptTemplate(
                input_variables=["activity"],
                template="Could you provide guidance on calculating insulin dosage based on {activity} carbohydrate intake?"
            )
            # st.write(f"selected the key_activity: {st.session_state.key_activity}")
            # ---- activity prompt ----/
            formatted_s_prompt = prompt_template.format(activity=new_glucose_level)
            #------------------------
            # memory.chat_memory.add_user_message(formatted_activity_prompt)
            memory.chat_memory.add_user_message(formatted_s_prompt)

            msgs.add_user_message(user_message)
            # Sample input values
            inputs = {
                "normal_gly": user_message
            }
            prompt_template_normal = PromptTemplate(
                input_variables=["normal_gly"],
                # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
                template="Could you provide guidance on calculating insulin dosage based on {normal_gly} carbohydrate intake ?"

            )
            memory.chat_memory.add_user_message(prompt_template_normal)
            st.session_state.formatted_activity_prompt_normal = prompt_template_normal

@st.fragment()
def frg_insulin():
        
    insulin = st.text_input("Carbohydrate content of meal in grams", on_change=update_ins_text, key="key_ins")
    # new_glucose_level_rounded = decimal_gl_txt.quantize(Decimal('0.0'), rounding=ROUND_DOWN)
    new_glucose_level = insulin

@st.fragment()
def frg_cgm_auto_update():

    duration_in_minutes = 5
    cgm = CGM(start_time = pd.Timestamp.now(), num_points=1, duration_in_minutes=duration_in_minutes)
    cg_data = cgm.cg_data


    # if "glucose_chart_session" in st.session_state:
    #     glucose_chart = st.session_state.glucose_chart_session
    # else:
    #     glucose_chart = cgm.initiate_cgm_chart()
    #     st.session_state.glucose_chart_session = glucose_chart
    
    # -- uncomment
    glucose_chart = cgm.initiate_cgm_chart()

    # Simulating dynamic data updates
    placeholder = st.empty()
    for i in range(200):  # Simulate 5 new data points coming in
        time.sleep(4)  # Simulating a time delay (can be removed for real-time updates)
        
        # Generate new data point
        new_time = pd.Timestamp.now() + pd.Timedelta(minutes=duration_in_minutes * (cgm.num_points+i))
        new_glucose_level = np.random.normal(loc=70, scale=30)


        # #------- glucose level above 70 normals ----

        # if new_glucose_level > 69:              
        #     user_message = "glucose level at :" + str(new_glucose_level) + "mg/dL"
        #     report_result = "Is this a normal range?"
        #     if st.session_state.cgm_user_normal_msg is None:    
        #         st.session_state.cgm_user_normal_msg  = user_message;  
        #          # -- call corpus 
        #         result = vectara.query_vectara("What it says about normal glucose level?")
        #         responses = result.get('responseSet', [])
        #         if responses:
        #             for i, response in enumerate(responses[0].get('response', []), 1):
        #                 print(f"\n{i}. {response.get('text')}")
        #                 report_result = response.get('text')
        #                 st.write(report_result)
        #                 break
        #         else:
        #             print("No results found.")
        #         st.write(user_message)
            

        #     if user_message:
        #         msgs.add_ai_message(user_message)
        #         # Sample input values
        #         inputs = {
        #             "report_result": report_result,
        #             "normal_gly": user_message
        #         }
        #         prompt_template_normal = PromptTemplate(
        #             input_variables=["report_result", "normal_gly"],
        #             # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
        #             template="Given my report: ""{report_result}"" do you want to check impact on my levels at {normal_gly} ?"

        #         )
                
        #         # ---- prompt_template_low_gly_sn1 prompt ----/
        #         formatted_activity_prompt_normal = prompt_template_normal.format(**inputs)
        #         #------------------------
        #         # memory.chat_memory.add_user_message(formatted_activity_prompt)
        #         memory.chat_memory.add_user_message(formatted_activity_prompt_normal)
        #         st.session_state.formatted_activity_prompt_normal = formatted_activity_prompt_normal


        # #------- glucose level hypo ----

        # if new_glucose_level <= 70:  
        #     user_message = "glucose level going below 70 at :" + str(new_glucose_level) + "mg/dL"
        #     if st.session_state.cgm_user_msg is None:    
        #         st.session_state.cgm_user_msg = user_message;  
        #         st.write(f"glucose going below 70")
        #         st.write(f"Say yes to agent for help...")
        #     # if st.session_state.low_glucose_level is None:
        #     #     st.session_state.low_glucose_level = new_glucose_level
        #     #     # Button to insert message
        #     #     if st.button("Take action", key="key_btn_low_gl", on_click=insert_cgm_message_agent, args=(new_glucose_level,)):
        #     #         pass
            
        #     # st.write(f"Inside cgm message {new_glucose_level}")
            
        #     if user_message:
        #         msgs.add_ai_message(user_message)
        #         prompt_template_low_gly_sn2 = PromptTemplate(
        #             input_variables=["low_gly_user_input_sn2"],
        #             template="Want other suggestions for fast acting carbohydrates for {low_gly_user_input_sn2} "
        #         )
                
        #         # ---- prompt_template_low_gly_sn2 prompt ----/
        #         formatted_activity_prompt_gl_sn2 = prompt_template_low_gly_sn2.format(low_gly_user_input_sn2 = user_message)
        #         #------------------------
        #         # memory.chat_memory.add_user_message(formatted_activity_prompt)
        #         memory.chat_memory.add_user_message(formatted_activity_prompt_gl_sn2)
        #         st.session_state.formatted_activity_prompt_gl_sn2 = formatted_activity_prompt_gl_sn2

        # #-------------------------------

        #  #------- glucose level hypo scenario 2 ----

        # if new_glucose_level <= 55:  
        #     user_message = "EMERGENCY"
        #     if st.session_state.cgm_user_msg1 is None:    
        #         st.session_state.cgm_user_msg1 = user_message;  
        #         st.write(f"Your blood sugar is danegerously low. Reach out for emergency glucogen kit. Call 911.")
        #         frg_emergency()
            
        #     if user_message:
        #         msgs.add_ai_message(user_message)
        #         prompt_template_low_gly_sn1 = PromptTemplate(
        #             input_variables=["low_gly_user_input_sn1"],
        #             # template="Your blood sugar is danegerously low. Reach out for emergency glucogen kit {low_gly_user_input_sn1}"
        #             template="Instructions on how to administer the glucogen during {low_gly_user_input_sn1} ?"

        #         )
                
        #         # ---- prompt_template_low_gly_sn1 prompt ----/
        #         formatted_activity_prompt_gl_sn1 = prompt_template_low_gly_sn1.format(low_gly_user_input_sn1 = user_message)
        #         #------------------------
        #         # memory.chat_memory.add_user_message(formatted_activity_prompt)
        #         memory.chat_memory.add_user_message(formatted_activity_prompt_gl_sn1)
        #         st.session_state.formatted_activity_prompt_gl_sn1 = formatted_activity_prompt_gl_sn1

        # #-------------------------------


        # Add the new data
        cg_data = cgm.add_new_data(cg_data, new_time, new_glucose_level)
        
        # Re-render the chart (in a real environment, this would dynamically refresh)
        glucose_chart = alt.Chart(cg_data).mark_line(point=True).encode(
            x='Time:T',
            y='Glucose Level (mg/dL):Q',
            tooltip=['Time:T', 'Glucose Level (mg/dL):Q']
        ).properties(
            title='Continuous Glucose Monitoring',
            width=600,
            height=300
        )
        with placeholder:
            st.altair_chart(glucose_chart, use_container_width=True)

# ---------------------- CGM ends -------------------------------------
col1, col2 = st.columns(2)



# -- emergency --
@st.fragment()
def frg_emergency(key="key_emergency"):
    if 'emergency_step' not in st.session_state:
        st.session_state.emergency_step = 0
        st.session_state.start_time = time.time()
    st.error(":rotating_light: EMERGENCY: Severe Hypoglycemia :rotating_light:")
    steps = ["Glucagon", "Call 911", "Wait"]
    animation_frames = [
        "  o   ",
        " /|\\  ",
        " / \\  ",
        "      ",
    ]
    progress = st.progress(0)
    status = st.empty()
    animation = st.empty()
    while st.session_state.emergency_step < len(steps):
        progress.progress((st.session_state.emergency_step + 1) / len(steps))
        status.write(f"Step {st.session_state.emergency_step + 1}: {steps[st.session_state.emergency_step]}")
        frame = animation_frames[st.session_state.emergency_step % len(animation_frames)]
        spaces = " " * (st.session_state.emergency_step * 10)
        animation.text(f"{spaces}{frame}")
        time.sleep(1)  # Simulate action time
        st.session_state.emergency_step += 1
        if st.session_state.emergency_step == 2:  # Wait step
            for i in range(5):  # 5 second wait
                animation.text(f"{spaces}{'.' * (i + 1)}")
                time.sleep(1)
    status.success("Emergency procedure completed!")
    animation.empty()
    elapsed_time = time.time() - st.session_state.start_time
    st.write(f"Total time: {elapsed_time:.1f} seconds")
    # if st.button("Reset", key=f"{key}_reset"):
    #     for key in ['emergency_step', 'start_time']:
    #         if key in st.session_state:
    #             del st.session_state[key]
    #     st.rerun()

# Usage in Streamlit app

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)



# Function to validate activity i/p
def validate_input(user_input):
    if user_input not in ["Yes", "Y", "Ok", "OK"]:
        memory.chat_memory.add_user_message("Check the activity with provider")
        return "Check with provider"
    else:
        # memory.chat_memory.add_user_message("Checking the user activity")
        return None

# if prompt := st.chat_input(placeholder= st.session_state.formatted_activity_prompt):
#     # # --validate activity ----
#     # validation_error = validate_input(prompt)
#     # if validation_error:
#     #     st.error(validation_error)
#     #     st.stop()
#     # else:
#     #     None

#     st.chat_message("user").write(st.session_state.formatted_activity_prompt)
#     if not openai_api_key:
#         st.info("Please add your OpenAI API key to continue.")
#         st.stop()

# #------- llm init end -----------/
#     # llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key, streaming=True)

#     chatagent = ChatAgent(llm_api_key=openai_api_key, model_name="gpt-4o-mini")
#     chatagent.initialize_chat()
#     llm = chatagent.get_agent()

# #------- llm init end -----------/
#     tools = [DuckDuckGoSearchRun(name="Search")]
#     chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)
#     executor = AgentExecutor.from_agent_and_tools(
#         agent=chat_agent,
#         tools=tools,
#         memory=memory,
#         return_intermediate_steps=True,
#         handle_parsing_errors=False,
#     )
#     with st.chat_message("assistant"):
#         st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
#         cfg = RunnableConfig()
#         cfg["callbacks"] = [st_cb]
#         response = executor.invoke(prompt, cfg)
#         st.write(response["output"])
#         st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

if prompt := st.chat_input(placeholder="Checking..."):
    st.chat_message("user").write(prompt)
    # st.chat_message("assistant").write(st.session_state.formatted_activity_prompt)
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key, streaming=True)
    tools = [DuckDuckGoSearchRun(name="Search")]
    chat_agent = ConversationalChatAgent.from_llm_and_tools(llm=llm, tools=tools)
    executor = AgentExecutor.from_agent_and_tools(
        agent=chat_agent,
        tools=tools,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )
    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]
        response = executor.invoke(prompt, cfg)
        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

with st.sidebar:
    st.markdown("# Prime health monitor") 
    # --- sugar i/p
    frg_cgm_text_update()
    if st.button("Get Support \u2665"):
        pass
    #----------
    st.write("Insulin dosage")
    frg_insulin()
    if st.button("Get insulin dose \u2665"):
        pass
    frg_option()
    if st.button("Ask Agent 🤖"):
        pass
    # frg_meal()
    # if st.button("Check plan 🗒️"):
        pass
    if st.button("Monitor and Ask Agent"):
        frg_cgm_auto_update()
        st.session_state.cgm_user_msg1 = None
    if st.button("Refresh"):
        msgs.clear()
        st.session_state.steps = {}
    