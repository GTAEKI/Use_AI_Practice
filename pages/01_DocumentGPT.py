import os, toml
import streamlit as st
from langchain.schema.output import ChatGenerationChunk, GenerationChunk
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, CacheBackedEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain.storage import LocalFileStore
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable  import RunnableLambda, RunnablePassthrough
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, AIMessage, HumanMessage

st.set_page_config(
    page_title="DocumentGPT",
    page_icon="📃"
)

## GitHub repo 링크
with st.sidebar:
    if st.sidebar.button("📌GitHub Link"):
        st.markdown('<meta http-equiv="refresh" content="0;URL=https://github.com/GTAEKI/Use_AI_Practice.git">',unsafe_allow_html=True)

## 사용자 API키 입력
with st.sidebar:
    secrets_path = f"./.streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        with open(secrets_path, "r", encoding = "utf-8") as secrets_file:
            secrets = toml.load(secrets_file)
    else:
        secrets = {}

    api_key = st.text_input("OpenAI API키를 입력하세요:", type="password")

    if st.button("API키 Save"):
        if api_key:
            secrets["OPENAI_API_KEY"] = api_key

            with open(secrets_path,"w",encoding="utf-8") as file:
                toml.dump(secrets,file)
            st.success("API 키가 저장되었습니다.")
        else:
            st.warning("API 키를 입력하세요.")

# callback handler는 event들을 listen하는 여러 function들을 가진다.
class ChatCallbackHandler(BaseCallbackHandler):
    message = ""

    def on_llm_start(self, *args, **kwargs):
        self.message_box = st.empty()
        with st.sidebar:
            st.write("llm started!")
    
    def on_llm_end(self, *args, **kwargs):
        save_message(self.message, "ai")
        with st.sidebar:
            st.write("llm ended!")

    def on_llm_new_token(self, token: str,*args,**kwargs):
        print(token)
        self.message += token
        self.message_box.markdown(self.message)

llm = ChatOpenAI(
    temperature=0.1,
    streaming=True,
    callbacks=[
        ChatCallbackHandler(),
    ],
)

# Memory
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    )


@st.cache_data(show_spinner="Embedding file...") # 아래 함수의 file이 변경되지 않으면 실행되지 않게함.
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    cache_dir = LocalFileStore(f"./.cache/embeddings/{file.name}")
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n",
        chunk_size = 600,
        chunk_overlap = 100,
    )
    loader = UnstructuredFileLoader(file_path)
    docs = loader.load_and_split(text_splitter=splitter)
    embeddings = OpenAIEmbeddings()
    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(embeddings, cache_dir)
    vectorstore = FAISS.from_documents(docs, cached_embeddings)
    retriever = vectorstore.as_retriever()
    return retriever

def save_message(message, role):
    st.session_state["messages"].append({"message":message, "role":role})

def send_message(message, role, save= True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message,role)

def paint_history():
    for message in st.session_state["messages"]:
        send_message(message["message"],message["role"],save=False)

def format_docs(docs):
    return "\n\n".join(document.page_content for document in docs)

def load_memory(_):
    return memory.load_memory_variables({})["chat_history"]


prompt = ChatPromptTemplate.from_messages([
    ("system","""
     Answer the question using Only the following context. If you don't know the answer just say you don't know. Don't make anything up.

     Context: {context}
     """),
     MessagesPlaceholder(variable_name="chat_history"),
    ("human","{question}")
])

st.title("DocumentGPT")

st.markdown("""
Welcome!
             
Use this chatbot to ask questions to an AI about your files!
            
사이드바에 파일을 업로드하세요.
"""
)

with st.sidebar:
    file = st.file_uploader("Upload a .txt .pdf or .docx file", type=["pdf","txt","docx"],
    )

if file:
    retriever = embed_file(file)
    send_message("I'm ready! Ask away!","ai", save=False)
    paint_history()
    message = st.chat_input("Ask anything about your file...")
    if message:
        send_message(message,"human")
        chain = {"context":retriever | RunnableLambda(format_docs),
                 "chat_history": load_memory,
                 "question": RunnablePassthrough()} | prompt | llm

        with st.chat_message("ai"):
            result = chain.invoke(message)
            memory.save_context({"input":message},{"output": result.content})

else:
    st.session_state["messages"] = []