from dotenv import load_dotenv
from langchain.schema.runnable import RunnableSequence
from utils.lm_studio import LMStudioLLM
from src.translation import translation_template
from src.routing import routing_template
from src.indexing import indexing_template
from src.raptor import raptor_template
from src.retrieval import retrieval_template
from src.generation import generation_template

from utils.pdf_summarizer import get_summaries

# Load environment variables
load_dotenv()

# Initialize LLM
lm_studio_llm = LMStudioLLM(path='completions')

# Input question
question = {'question': "What is twitter sentiment analysis?"}

# Precompute translation_output
translation_result = translation_template() | lm_studio_llm
translation_output = translation_result.invoke(question)

# Gather files
files = ["1", "2", "3"]
# for i in range(int(input("Enter the number of files: "))):
#     files.append(input("Enter file name: "))

# Generate file summaries
file_summaries = ""
if len(files) > 0:
    # summaries in the format [[file_name, summary], ..]
    summaries = get_summaries(files)
    file_summaries = "\n".join([f"{file}: {summary}" for file, summary in summaries])

# Define llm_chain_file
llm_chain_file = RunnableSequence(
    (lambda question: routing_template().format(
        question=question['question'],  
        file_summaries=file_summaries  
    )) | 
    lm_studio_llm | 
    (lambda doc_list: [
        doc.page_content for doc in indexing_template()(
            documents=doc_list,
            questions=translation_output  
        )
    ]) 
)

# Define llm_chain_no_file
llm_chain_no_file = RunnableSequence(
    translation_template() | lm_studio_llm
)

# Execute chain based on files
if len(files) == 0:
    answer = llm_chain_no_file.invoke(question)
else:
    answer = llm_chain_file.invoke({
        'question': question,
        'file_summaries': file_summaries
    })

print(answer)