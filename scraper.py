"""
Web scraping module for extracting game schedules and team contacts.
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import List, Dict, Optional
from dateutil import parser
from contacts_parser import ContactsParser
import config

logger = logging.getLogger(__name__)


class WebScraper:
    """Handles web scraping operations for schedule and contacts pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(config.REQUEST_HEADERS)
        self.contacts_parser = ContactsParser()
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse HTML content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching content from {url}")
            response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            logger.info(f"Successfully fetched content from {url}")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def extract_sunday_games(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract future Sunday games for SPARTA XI from the schedule page.
        
        Args:
            soup: BeautifulSoup object of the schedule page
            
        Returns:
            List of dictionaries containing game information
        """
        games = []
        today = date.today()
        
        try:
            # Find the "UPCOMING MATCHES" section
            upcoming_section = self._find_upcoming_matches_section(soup)
            if not upcoming_section:
                logger.warning("Could not find 'UPCOMING MATCHES' section")
                return []
            
            # Find all schedule entries within the upcoming section
            schedule_entries = upcoming_section.find_all('div', class_='schedule-all')
            logger.info(f"Found {len(schedule_entries)} schedule entries in upcoming section")
            
            for i, entry in enumerate(schedule_entries):
                logger.info(f"Processing entry {i+1}/{len(schedule_entries)}")
                
                # Debug: Print the entry structure
                entry_text = entry.get_text()[:200] + "..." if len(entry.get_text()) > 200 else entry.get_text()
                logger.info(f"Entry text preview: {entry_text}")
                
                game_info = self._parse_game_entry(entry)
                
                if game_info:
                    if self._is_valid_sunday_game(game_info, today):
                        games.append(game_info)
                        logger.info(f"Found Sunday game: {game_info['opponent']} on {game_info['date']}")
                    else:
                        logger.info(f"Game found but not a valid Sunday game: {game_info['opponent']} on {game_info['date']} (weekday: {game_info['date'].weekday()})")
                else:
                    logger.warning(f"Failed to parse game entry {i+1}")
            
            logger.info(f"Found {len(games)} future Sunday games for {config.TEAM_NAME}")
            return games
            
        except Exception as e:
            logger.error(f"Error extracting games: {e}")
            return []
    
    def _find_upcoming_matches_section(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Find the section containing upcoming matches.
        
        Args:
            soup: BeautifulSoup object of the schedule page
            
        Returns:
            BeautifulSoup element containing upcoming matches or None
        """
        try:
            # Look for the "UPCOMING MATCHES" button
            upcoming_buttons = soup.find_all('span', string=lambda text: text and 'UPCOMING MATCHES' in text.upper())
            
            if not upcoming_buttons:
                logger.warning("Could not find 'UPCOMING MATCHES' button")
                return None
            
            # Find the closest parent container that contains the upcoming matches
            for button in upcoming_buttons:
                # Navigate up to find the container with schedule entries
                container = button
                for _ in range(10):  # Limit the search depth
                    container = container.parent
                    if not container:
                        break
                    
                    # Check if this container has schedule entries
                    if container.find('div', class_='schedule-all'):
                        logger.info("Found upcoming matches section")
                        return container
            
            logger.warning("Could not find container with upcoming matches")
            return None
            
        except Exception as e:
            logger.error(f"Error finding upcoming matches section: {e}")
            return None
    
    def _parse_game_entry(self, entry) -> Optional[Dict]:
        """
        Parse individual game entry to extract opponent, date, and team logo.
        
        Args:
            entry: BeautifulSoup element containing game information
            
        Returns:
            Dictionary with opponent, date, and logo URL, or None if parsing fails
        """
        try:
            logger.info("Starting to parse game entry...")
            
            # Extract game date
            game_date = self._extract_date(entry)
            if not game_date:
                logger.warning("Failed to extract game date")
                return None
            
            logger.info(f"Extracted date: {game_date}")
            
            # Extract opponent team name and logo
            opponent_info = self._extract_opponent_and_logo(entry)
            if not opponent_info:
                logger.warning("Failed to extract opponent info")
                return None
            
            logger.info(f"Extracted opponent: {opponent_info['name']}")
            logger.info(f"Extracted opponent logo: {opponent_info['logo']}")
            logger.info(f"Extracted SPARTA logo: {opponent_info['sparta_logo']}")
            
            return {
                'opponent': opponent_info['name'],
                'date': game_date,
                'opponent_logo': opponent_info['logo'],
                'sparta_logo': opponent_info['sparta_logo']
            }
            
        except Exception as e:
            logger.error(f"Error parsing game entry: {e}")
        
        return None
    
    def _extract_date(self, entry) -> Optional[date]:
        """Extract game date from game entry."""
        try:
            # Find the schedule time div
            time_div = entry.find('div', class_='sch-time')
            if not time_div:
                logger.warning("Could not find sch-time div")
                return None
            
            # Extract day, date, month, year
            day_elem = time_div.find('h4')
            date_elem = time_div.find('h2')
            month_year_elem = time_div.find('h5')
            
            if not all([day_elem, date_elem, month_year_elem]):
                logger.warning(f"Missing date elements: day={day_elem}, date={date_elem}, month_year={month_year_elem}")
                return None
            
            day_name = day_elem.get_text().strip()
            day_num = date_elem.get_text().strip()
            month_year = month_year_elem.get_text().strip()
            
            logger.info(f"Date components: day={day_name}, date={day_num}, month_year={month_year}")
            
            # Parse the date components
            try:
                # Format: "Aug 2025" -> parse to get month and year
                month_str, year_str = month_year.split()
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                
                month = month_map.get(month_str, 1)
                year = int(year_str)
                day = int(day_num)
                
                game_date = date(year, month, day)
                
                # Verify it's the correct day of week
                if game_date.strftime('%A') == day_name:
                    logger.info(f"Successfully parsed date: {game_date}")
                    return game_date
                else:
                    logger.warning(f"Day mismatch: expected {day_name}, got {game_date.strftime('%A')}")
                    return None
                    
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing date components: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting date: {e}")
            return None
    
    def _extract_opponent_and_logo(self, entry) -> Optional[Dict]:
        """Extract opponent team name and logo from game entry."""
        try:
            # Find the schedule text div
            text_div = entry.find('div', class_='schedule-text')
            if not text_div:
                logger.warning("Could not find schedule-text div")
                return None
            
            # Find the h3 element containing team names
            h3_elem = text_div.find('h3')
            if not h3_elem:
                logger.warning("Could not find h3 element in schedule-text")
                return None
            
            # Extract team names from links, but filter out empty ones
            team_links = h3_elem.find_all('a')
            valid_team_links = []
            
            for link in team_links:
                team_name = link.get_text().strip()
                if team_name and team_name.lower() not in ['v', 'vs', 'versus']:
                    valid_team_links.append(link)
            
            if len(valid_team_links) < 2:
                logger.warning(f"Not enough valid team links found: {len(valid_team_links)}")
                return None
            
            logger.info(f"Found {len(valid_team_links)} valid team links")
            
            # Find logos in the schedule-logo div
            logo_div = entry.find('div', class_='schedule-logo')
            logo_imgs = logo_div.find_all('img') if logo_div else []
            
            logger.info(f"Found {len(logo_imgs)} logo images")
            
            opponent_name = None
            opponent_logo = None
            sparta_logo = None
            
            # Extract team names and match with logos
            for i, link in enumerate(valid_team_links):
                team_name = link.get_text().strip()
                logger.info(f"Valid team {i+1}: {team_name}")
                
                if team_name.lower() == config.TEAM_NAME.lower():
                    # This is SPARTA XI
                    if i < len(logo_imgs):
                        sparta_logo = logo_imgs[i].get('src')
                        logger.info(f"SPARTA XI logo: {sparta_logo}")
                else:
                    # This is the opponent
                    opponent_name = team_name
                    if i < len(logo_imgs):
                        opponent_logo = logo_imgs[i].get('src')
                        logger.info(f"Opponent logo: {opponent_logo}")
            
            if opponent_name and opponent_logo:
                logger.info(f"Successfully extracted opponent: {opponent_name}")
                return {
                    'name': opponent_name,
                    'logo': opponent_logo,
                    'sparta_logo': sparta_logo
                }
            else:
                logger.warning(f"Missing opponent info: name={opponent_name}, logo={opponent_logo}")
            
        except Exception as e:
            logger.error(f"Error extracting opponent and logo: {e}")
        
        return None
    
    def _is_valid_sunday_game(self, game_info: Dict, today: date) -> bool:
        """
        Check if the game is a valid future Sunday game.
        
        Args:
            game_info: Dictionary containing game information
            today: Current date
            
        Returns:
            True if valid Sunday game in the future
        """
        game_date = game_info['date']
        
        # Check if it's in the future
        if game_date <= today:
            return False
        
        # Check if it's a Sunday (weekday 6)
        if game_date.weekday() != 6:  # Sunday is weekday 6
            return False
        
        return True
    
    def get_team_contact(self, team_name: str) -> Optional[List[str]]:
        """
        Get contact emails for a specific team using direct parsing.
        
        Args:
            team_name: Name of the team to find contact for
            
        Returns:
            List of email addresses or None if not found
        """
        return self.contacts_parser.get_team_contact(team_name)
    
    def get_all_team_contacts(self) -> Dict[str, List[str]]:
        """
        Get all team contacts using direct parsing.
        
        Returns:
            Dictionary mapping team names to lists of email addresses
        """
        return self.contacts_parser.get_all_team_contacts() 