"""
Contacts parser module for extracting team contact information from tab-separated file.
"""

import logging
import csv
from typing import Dict, List, Optional
import config
import os

logger = logging.getLogger(__name__)


class ContactsParser:
    """Handles parsing of team contacts from tab-separated file."""
    
    def __init__(self):
        self.contacts_data = {}
        self._load_contacts()
    
    def _load_contacts(self):
        """Load contacts from the tab-separated file."""
        try:
            logger.info(f"Attempting to load contacts from: {config.CONTACTS_FILE}")
            
            with open(config.CONTACTS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Skip the title line "Team Contacts"
                if lines and lines[0].strip() == "Team Contacts":
                    lines = lines[1:]
                    logger.info("Skipped title line: Team Contacts")
                
                if not lines:
                    logger.error("No data lines found after skipping title")
                    return
                
                # Parse the header line
                header_line = lines[0].strip()
                headers = header_line.split('\t')
                logger.info(f"Headers: {headers}")
                
                # Find the column indices
                team_index = None
                captain_email_index = None
                vice_captain_email_index = None
                
                for i, header in enumerate(headers):
                    if header == 'Team':
                        team_index = i
                    elif header == 'Captain Email':
                        captain_email_index = i
                    elif header == 'Vice Captain Email':
                        vice_captain_email_index = i
                
                if team_index is None:
                    logger.error("Could not find 'Team' column in headers")
                    return
                
                logger.info(f"Column indices - Team: {team_index}, Captain Email: {captain_email_index}, Vice Captain Email: {vice_captain_email_index}")
                
                # Process data rows (skip header)
                for row_num, line in enumerate(lines[1:], 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Split by tab
                    fields = line.split('\t')
                    logger.info(f"Processing row {row_num}: {fields}")
                    
                    # Extract team name
                    if len(fields) <= team_index:
                        logger.warning(f"Row {row_num}: Not enough fields for team index")
                        continue
                    
                    team_name = fields[team_index].strip()
                    if not team_name:
                        logger.warning(f"Row {row_num}: Empty team name, skipping")
                        continue
                    
                    # Extract email addresses
                    emails = []
                    
                    # Captain email
                    if captain_email_index is not None and len(fields) > captain_email_index:
                        captain_email = fields[captain_email_index].strip()
                        if captain_email and self._is_valid_email(captain_email):
                            emails.append(captain_email)
                            logger.info(f"Added captain email: {captain_email}")
                        elif captain_email:
                            logger.warning(f"Invalid captain email: {captain_email}")
                    
                    # Vice Captain email
                    if vice_captain_email_index is not None and len(fields) > vice_captain_email_index:
                        vice_captain_email = fields[vice_captain_email_index].strip()
                        if vice_captain_email and self._is_valid_email(vice_captain_email):
                            emails.append(vice_captain_email)
                            logger.info(f"Added vice captain email: {vice_captain_email}")
                        elif vice_captain_email:
                            logger.warning(f"Invalid vice captain email: {vice_captain_email}")
                    
                    if emails:
                        self.contacts_data[team_name] = emails
                        logger.info(f"Loaded contacts for {team_name}: {emails}")
                    else:
                        logger.warning(f"No valid emails found for team: {team_name}")
                
                logger.info(f"Successfully loaded contacts for {len(self.contacts_data)} teams")
                logger.info(f"Available teams: {list(self.contacts_data.keys())}")
                
        except FileNotFoundError:
            logger.error(f"Contacts file not found: {config.CONTACTS_FILE}")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info("Please ensure contacts.txt exists in the project root")
        except Exception as e:
            logger.error(f"Error loading contacts: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.match(email_pattern, email))
    
    def get_team_contact(self, team_name: str) -> Optional[List[str]]:
        """
        Get contact emails for a specific team.
        
        Args:
            team_name: Name of the team to find contact for
            
        Returns:
            List of email addresses or None if not found
        """
        # Try exact match first
        if team_name in self.contacts_data:
            emails = self.contacts_data[team_name]
            logger.info(f"Found exact match for {team_name}: {emails}")
            return emails
        
        # Try partial match (case-insensitive)
        team_name_lower = team_name.lower()
        for stored_team, emails in self.contacts_data.items():
            if team_name_lower in stored_team.lower() or stored_team.lower() in team_name_lower:
                logger.info(f"Found partial match: '{team_name}' matches '{stored_team}': {emails}")
                return emails
        
        logger.warning(f"No contact found for team: {team_name}")
        return None
    
    def get_all_team_contacts(self) -> Dict[str, List[str]]:
        """
        Get all team contacts.
        
        Returns:
            Dictionary mapping team names to lists of email addresses
        """
        return self.contacts_data.copy()
    
    def list_all_teams(self) -> List[str]:
        """
        Get list of all team names in contacts file.
        
        Returns:
            List of team names
        """
        return list(self.contacts_data.keys()) 