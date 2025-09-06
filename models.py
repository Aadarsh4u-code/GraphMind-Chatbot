from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
import os


from dotenv import load_dotenv


load_dotenv()

hugging_face_llm = HuggingFacePipeline.from_model_id(
    model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    # huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    task="text-generation",
    pipeline_kwargs=dict(
        temperature=0.5,
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.03,
        return_full_text=False
        
    ),
)

local_llm = ChatHuggingFace(llm=hugging_face_llm)