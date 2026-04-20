"""
Unit tests for utils module
"""
import pytest
from src.utils import Review, ExtractedData, load_reviews, save_results
import pandas as pd
import json
from pathlib import Path
import tempfile

class TestReview:
    def test_review_creation(self):
        """Test Review model creation"""
        review = Review(review_id="1", review_text="Great product!")
        assert review.review_id == "1"
        assert review.review_text == "Great product!"
    
    def test_review_validation_missing_field(self):
        """Pydantic v2 raises ValidationError when a required field is missing."""
        with pytest.raises(Exception):
            Review(review_id="123")  # review_text is missing — must raise

class TestExtractedData:
    def test_extracted_data_creation(self):
        """Test ExtractedData model creation"""
        data = ExtractedData(
            review_id="1",
            product="Coffee Maker",
            sentiment="positive",
            reason="Works great",
            confidence=0.95,
            prompt_used="baseline"
        )
        assert data.review_id == "1"
        assert data.product == "Coffee Maker"
        assert data.sentiment == "positive"
        assert data.confidence == 0.95
    
    def test_confidence_range(self):
        """Test confidence validation""" 
        # Valid confidence
        data = ExtractedData(
            review_id="1",
            product="Test",
            sentiment="positive",
            reason="Good",
            confidence=0.75,
            prompt_used="test"
        )
        assert 0 <= data.confidence <= 1

class TestLoadReviews:
    def test_load_reviews_valid_csv(self):
        """Test loading reviews from valid CSV"""
        # Create temp CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("review_id,review_text\n")
            f.write("1,Great product\n")
            f.write("2,Not good\n")
            temp_path = f.name
        
        try:
            df = load_reviews(temp_path)
            assert len(df) == 2
            assert 'review_id' in df.columns
            assert 'review_text' in df.columns
        finally:
            Path(temp_path).unlink()
    
    def test_load_reviews_missing_file(self):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            load_reviews("nonexistent.csv")

class TestSaveResults:
    def test_save_results(self):
        """Test saving results to JSON"""
        results = [
            ExtractedData(
                review_id="1",
                product="Test",
                sentiment="positive",
                reason="Good",
                confidence=0.9,
                prompt_used="test"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            save_results(results, temp_path)
            
            # Verify file exists and has content
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['review_id'] == "1"
            assert data[0]['product'] == "Test"
        finally:
            Path(temp_path).unlink()
