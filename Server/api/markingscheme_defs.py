import tempfile
import os
import json
import re
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
import ollama



def extract_text_from_file(self, file_path, file_extension):
        """Extract text from different file types."""
        if file_extension == '.docx':
            # Use the existing document parsing logic from functions.py
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            
        elif file_extension == '.pdf':
            # Use the existing PDF parsing logic
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
            
        elif file_extension == '.xlsx':
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # Try to detect relevant columns
            headers = [str(col).lower() for col in df.columns]
            text_representation = ""
            
            # Check if we can identify question/answer columns
            q_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['question', 'prompt'])), None)
            a_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['answer', 'response', 'solution'])), None)
            m_col = next((i for i, h in enumerate(headers) if any(x in h for x in ['mark', 'score', 'point'])), None)
            
            # Format as text for the AI to process
            for idx, row in df.iterrows():
                line = f"{idx+1}. "
                if q_col is not None and pd.notna(row.iloc[q_col]):
                    line += f"Question: {row.iloc[q_col]} "
                if a_col is not None and pd.notna(row.iloc[a_col]):
                    line += f"Answer: {row.iloc[a_col]} "
                if m_col is not None and pd.notna(row.iloc[m_col]):
                    line += f"Marks: {row.iloc[m_col]}"
                text_representation += line + "\n"
                
            return text_representation
            
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    

def parse_with_ollama(self, content):
        """Use Ollama to parse the content into structured marking scheme data."""
        system_prompt = """
        You are an expert at analyzing educational content and creating marking schemes. Your task is to extract a structured marking scheme from the provided content.
        
        Please extract:
        1. Question number (required)
        2. Question text if present
        3. Answer text (required)
        4. Marks/points value if specified
        5. Appropriate grading type based on the answer
        
        For grading types:
        - "one-word": Use for single word or very short (1-2 words) answers
        - "short-phrase": Use for sentence answers that require meaning comparison
        - "list": Use when the answer contains multiple items or is comma-separated
        - "numerical": Use for numbers, calculations, or numeric ranges
        
        Return a well-structured JSON array with each question as an object. Include only questions where you can confidently extract an answer.
        
        Output format:
        [
          {
            "number": 1,
            "question": "What is the capital of France?",
            "answer": "Paris",
            "marks": 5,
            "gradingType": "one-word"
          },
          ...
        ]
        
        If marks are not specified, omit the "marks" field. If question text isn't available, include an empty string for "question".
        """
        
        user_prompt = f"""
        Please create a structured marking scheme from the following content. Extract all questions and answers:
        
        {content}
        
        Return only JSON with no additional text.
        """
        
        try:
            # Use the existing Ollama integration from functions.py
            response = ollama.chat(
                model="qwen2.5:1.5b",  # Using the model specified in your existing code
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            
            # Extract the JSON response
            response_content = response["message"]["content"].strip()
            
            # Try to extract just the JSON array
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # Try parsing the entire content as JSON
                return json.loads(response_content)
                
        except Exception as e:
            logger.error(f"Error parsing with Ollama: {e}")
            # If parsing fails, try a more structured approach
            return self.fallback_parsing(content)
    
def fallback_parsing(self, content):
        """Fallback method if the AI parsing fails, using regex patterns."""
        items = []
        
        # Common patterns for numbered items
        patterns = [
            r'(\d+)[.)]?\s+(.+?)(?=\n\d+[.)]|\Z)',  # Standard numbered format: "1. Answer"
            r'Q(?:uestion)?\s*(\d+)[.:]?\s+(.+?)(?=Q(?:uestion)?\s*\d+|$)',  # Q1 format
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                number = int(match.group(1))
                answer_text = match.group(2).strip()
                
                # Skip if already found this question number
                if any(item['number'] == number for item in items):
                    continue
                    
                # Look for marks in the answer text
                marks_match = re.search(r'\((\d+)\s*marks?\)', answer_text, re.IGNORECASE)
                marks = None
                if marks_match:
                    marks = int(marks_match.group(1))
                    # Remove the marks text from the answer
                    answer_text = re.sub(r'\((\d+)\s*marks?\)', '', answer_text).strip()
                
                # Basic item with defaults
                item = {
                    'number': number,
                    'question': "",
                    'answer': answer_text,
                }
                
                if marks:
                    item['marks'] = marks
                
                # Try to infer grading type
                if re.match(r'^\d+(\.\d+)?$', answer_text):
                    item['gradingType'] = 'numerical'
                elif ',' in answer_text and len(answer_text.split(',')) > 1:
                    item['gradingType'] = 'list'
                elif len(answer_text.split()) > 3:
                    item['gradingType'] = 'short-phrase'
                else:
                    item['gradingType'] = 'one-word'
                
                items.append(item)
        
        return items
    
def process_parsed_items(self, parsed_items):
        """Process parsed items and apply defaults where needed."""
        processed_items = []
        
        for item in parsed_items:
            # Skip items without required fields
            if 'number' not in item or 'answer' not in item:
                continue
                
            # Ensure the answer is not empty
            if not item.get('answer', '').strip():
                continue
                
            # Create a new item with defaults
            processed_item = {
                'number': item.get('number'),
                'question': item.get('question', ""),
                'answer': item.get('answer'),
                'marks': item.get('marks', 10),  # Default to 10 marks as specified
                'gradingType': item.get('gradingType', 'one-word')
            }
            
            # Set smart defaults based on content
            if processed_item['gradingType'] == 'one-word':
                # If answer has capital letters, make it case sensitive
                processed_item['caseSensitive'] = any(c.isupper() for c in processed_item['answer'])
            elif processed_item['gradingType'] == 'list':
                processed_item['partialMatching'] = True  # Enable partial matching for lists
            elif processed_item['gradingType'] == 'numerical':
                processed_item['rangeSensitive'] = True  # Enable range for numerical
            
            processed_items.append(processed_item)
        
        return processed_items