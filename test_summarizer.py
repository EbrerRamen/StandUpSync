from transformers import pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_summarizer():
    try:
        logger.info("Loading summarization model...")
        summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1
        )
        logger.info("Model loaded successfully!")
        
        test_text = """
        Yesterday was quite productive. I started by reviewing the pull requests from the team and provided feedback on three different features. 
        After that, I spent most of the morning debugging the authentication system that was causing issues for some users. 
        The main problem was related to token expiration handling, which I was able to fix by implementing a more robust refresh token mechanism.
        """
        
        logger.info("Testing summarization...")
        summary = summarizer(test_text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        logger.info(f"Generated summary: {summary}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing summarizer: {str(e)}")
        return False

if __name__ == "__main__":
    test_summarizer() 