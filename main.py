"""
Main application module for biweekly task automation.
"""

import logging
from datetime import date
from typing import Dict
from scraper import WebScraper
from email_manager import EmailManager
from contacts_parser import ContactsParser
import config

logger = logging.getLogger(__name__)


class BiweeklyTaskAutomation:
    """Main application class for automating biweekly tasks."""
    
    def __init__(self):
        self.scraper = WebScraper()
        self.email_manager = EmailManager()
        self.contacts_parser = ContactsParser()
    
    def run(self) -> bool:
        """
        Run the complete biweekly task automation.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting biweekly task automation")
            
            # Step 1: Scrape the schedule page
            soup = self.scraper.get_page_content(config.SCHEDULE_URL)
            if not soup:
                logger.error("Failed to fetch schedule page")
                return False
            
            # Step 2: Extract Sunday games
            games = self.scraper.extract_sunday_games(soup)
            if not games:
                logger.info("No future Sunday games found")
                return True
            
            logger.info(f"Found {len(games)} future Sunday games")
            
            # Step 3: Process each game
            success_count = 0
            for game in games:
                if self._process_game(game):
                    success_count += 1
            
            logger.info(f"Successfully processed {success_count}/{len(games)} games")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error in biweekly task automation: {e}")
            return False
    
    def _process_game(self, game: Dict) -> bool:
        """
        Process a single game: get contacts and schedule email.
        
        Args:
            game: Dictionary containing game information
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            opponent_team = game['opponent']
            game_date = game['date']
            
            logger.info(f"Processing game: {opponent_team} on {game_date}")
            
            # Step 1: Get team contact using direct parsing
            contact_emails = self.contacts_parser.get_team_contact(opponent_team)
            if not contact_emails:
                logger.error(f"No contact found for team: {opponent_team}")
                return False
            
            logger.info(f"Found {len(contact_emails)} contact(s) for {opponent_team}: {contact_emails}")
            
            # Step 2: Skip Saturday games (away games)
            if game_date.weekday() == 5:  # Saturday is weekday 5
                logger.info(f"Skipping Saturday game: {opponent_team} on {game_date}")
                return True
            
            # Step 3: Schedule invitation email
            success = self.email_manager.draft_game_invitation(game, contact_emails)
            
            if success:
                logger.info(f"Successfully scheduled invitation for {opponent_team}")
                logger.info(f"Email subject: {config.EMAIL_SUBJECT_FORMAT.format(OPPONENT_TEAM=opponent_team)}")
            else:
                logger.error(f"Failed to schedule invitation for {opponent_team}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing game {game}: {e}")
            return False


def main():
    """Main entry point for the application."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    # Create and run the automation
    automation = BiweeklyTaskAutomation()
    success = automation.run()
    
    if success:
        logger.info("✅ Biweekly task automation completed successfully")
    else:
        logger.error("❌ Biweekly task automation failed")
    
    return success


if __name__ == "__main__":
    main() 