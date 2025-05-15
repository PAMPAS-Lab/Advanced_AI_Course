import re
import arxiv
import fitz
from ast import literal_eval


def load_prompt(file):
    prompt = ""
    with open(file) as f:
        for line in f:
            prompt += line
    return prompt

def normalize_doc(doc):
    paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
    return paragraphs

def get_reference_titles(paragraphs):
    titles = []
    ref_index = paragraphs.index("参考文献")
    references = paragraphs[ref_index+1:]
    pattern = r'\.\s*([^\.]+?)\s*\[[A-Z]\]'
    for ref in references:
        match = re.search(pattern, ref)
        if match:
            title = match.group(1).strip()
            titles.append(title)
    return titles

def get_citation_markers(paragraphs):
    def map_citation_to_text(text):
        citation_to_text = []
        pattern = r'\[(\s*\d+(\s*,\s*\d+)*)\s*\]'
        matches = re.finditer(pattern, text)
        if matches:
            for match in matches:
                start, end = match.start(), match.end()
                while start - 1 >= 0 and text[start - 1] != "。":
                    start -= 1
                while end <= len(text) - 1 and text[end] != "。":
                    end += 1
                citation_text = text[start: end + 1]
                citation = literal_eval(match.group())
                citation_to_text.append((citation, citation_text))
        return citation_to_text
    all_citation_to_text= []
    for paragraph in paragraphs:
        citation_to_text = map_citation_to_text(paragraph)
        all_citation_to_text.extend(citation_to_text)
    return all_citation_to_text

def load_pdf(files):
    text = ""
    if isinstance(files, list):
        for file in files:
            pdf = fitz.open(file)
            for page_index in range(len(pdf)):
                page = pdf.load_page(page_index)
                text += page.get_text()
        return text
    else:
        print("references应该为list类型")

def search_from_arxiv(query):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=5
    )
    return client.results(search)










