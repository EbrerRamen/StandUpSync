from transformers import pipeline
from django.conf import settings
import logging
import os
import openai

logger = logging.getLogger(__name__)

def get_summarizer():
    """
    Returns a summarization pipeline using the BART model.
    The model is loaded only once and cached for subsequent calls.
    """
    if not hasattr(get_summarizer, 'summarizer'):
        try:
            get_summarizer.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1  # Use CPU. Change to 0 for GPU if available
            )
        except Exception as e:
            logger.error(f"Error loading summarization model: {str(e)}")
            return None
    return get_summarizer.summarizer

def summarize_text(text):
    """
    Summarizes the given text using the BART model.
    
    Args:
        text (str): The text to summarize
        
    Returns:
        str: The summarized text, or None if summarization fails
    """
    if not text or not text.strip():
        return None
        
    try:
        summarizer = get_summarizer()
        if not summarizer:
            logger.error("Failed to load summarizer")
            return None
            
        # Split text into chunks if it's too long (BART has a max input length)
        max_chunk_length = 1024
        chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        summaries = []
        for chunk in chunks:
            summary = summarizer(
                chunk,
                max_length=130,
                min_length=30,
                do_sample=False
            )[0]['summary_text']
            summaries.append(summary)
            
        return ' '.join(summaries)
        
    except Exception as e:
        logger.error(f"Error during text summarization: {str(e)}")
        return None

def summarize_text_old(text, max_length=130, min_length=30):
    """
    Summarizes the given text using the BART model.
    
    Args:
        text (str): The text to summarize
        max_length (int): Maximum length of the summary
        min_length (int): Minimum length of the summary
        
    Returns:
        str: The summarized text, or the original text if summarization fails
    """
    if not text or len(text.strip()) < 100:  # Don't summarize very short texts
        return text
        
    try:
        summarizer = get_summarizer()
        if not summarizer:
            return text
            
        # Split text into chunks if it's too long (BART has a max input length)
        max_chunk_length = 1024
        chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]
        
        summaries = []
        for chunk in chunks:
            summary = summarizer(
                chunk,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )[0]['summary_text']
            summaries.append(summary)
            
        return ' '.join(summaries)
        
    except Exception as e:
        logger.error(f"Error during text summarization: {str(e)}")
        return text 