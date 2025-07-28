#!/usr/bin/env python3
"""
Test script to verify draft saving functionality.
"""

import logging
from email_manager import EmailManager
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_draft_saving():
    """Test draft saving functionality."""
    print("🧪 Testing draft saving functionality...")
    
    # Create email manager
    email_manager = EmailManager()
    
    # Test data
    from datetime import date
    test_game_info = {
        'opponent': 'Test Team',
        'date': date(2025, 8, 10),  # Use date object instead of string
        'opponent_logo': 'https://media.cricclubs.com/documentsRep/teamLogos/6dc8ed6f-1418-4922-ad7b-c79a929303c5.jpg',
        'sparta_logo': 'https://media.cricclubs.com/documentsRep/teamLogos/b035e4ff-ed87-4f30-96b8-17b4d52f6d55.jpg'
    }
    
    test_contacts = ['test@example.com']
    
    print("📧 Testing game invitation draft creation...")
    
    # Test the draft_game_invitation method (which now saves as draft)
    success = email_manager.draft_game_invitation(test_game_info, test_contacts)
    
    if success:
        print("✅ Draft saved successfully!")
        print("📝 Check your Gmail drafts folder for the test email")
        return True
    else:
        print("❌ Failed to save draft")
        return False

if __name__ == "__main__":
    success = test_draft_saving()
    if success:
        print("\n🎉 Draft saving test passed!")
    else:
        print("\n💥 Draft saving test failed!") 