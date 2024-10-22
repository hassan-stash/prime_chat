Prime Health 

An AI agent to manage diabetes plans. 

Setup:
pip install requirements:
  streamlit
  openai
  langchain

To run:
set up .toml:
  Add .streamlit/secrets.toml in root if not exists
  Add :
     OpenAI_key = "<LLM_PROVIDER_KEY>"
     RAG_provider_api_key = "<corpus_key_general>"
     RAG_document_diabetes_pan_api_key = "<corpus_key_plan>"
  pip install -r requirements. txt   
  run:> streamlit run streamlit_app.py