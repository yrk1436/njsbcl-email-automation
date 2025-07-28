"""
LLM-based contact extraction module using Ollama.
Extracts team contact information from contacts.txt file.
"""

import logging
import requests
import json
from typing import Optional, Dict, List
import config

logger = logging.getLogger(__name__)


class LLMContactExtractor:
    """Extracts team contact information using Ollama LLM."""
    
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Make a call to Ollama API.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response from Ollama or None if failed
        """
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            logger.info(f"Calling Ollama with model: {self.model}")
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            return None
    
    def load_contacts_file(self) -> Optional[str]:
        """
        Load the contacts.txt file.
        
        Returns:
            File content as string or None if failed
        """
        try:
            with open(config.CONTACTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Successfully loaded {config.CONTACTS_FILE}")
            return content
        except FileNotFoundError:
            logger.error(f"Contacts file not found: {config.CONTACTS_FILE}")
            return None
        except Exception as e:
            logger.error(f"Error loading contacts file: {e}")
            return None
    
    def extract_team_contact(self, team_name: str) -> Optional[List[str]]:
        """
        Extract contact emails for a specific team using LLM.
        
        Args:
            team_name: Name of the team to find contact for
            
        Returns:
            List of email addresses or None if not found
        """
        # Load contacts file
        contacts_content = self.load_contacts_file()
        if not contacts_content:
            return None
        
        # Create prompt for the LLM
        prompt = self._create_extraction_prompt(team_name, contacts_content)
        
        # Call Ollama
        response = self._call_ollama(prompt)
        if not response:
            return None
        
        # Parse the response
        emails = self._parse_llm_response(response)
        
        if emails:
            logger.info(f"Found {len(emails)} contact(s) for {team_name}: {emails}")
        else:
            logger.warning(f"No contact found for team: {team_name}")
        
        return emails
    
    def _create_extraction_prompt(self, team_name: str, contacts_content: str) -> str:
        """
        Create a prompt for the LLM to extract team contact.
        
        Args:
            team_name: Name of the team to search for
            contacts_content: Content of the contacts file
            
        Returns:
            Formatted prompt for the LLM
        """
        return f"""You are a helpful assistant that extracts email addresses from contact information.

Given the following contacts file content, find ALL email addresses for the team "{team_name}".

Contacts file content:
{contacts_content}

Instructions:
1. Look for the team name "{team_name}" (case-insensitive, partial matches are okay)
2. Extract ALL email addresses associated with that team
3. Return the emails as a comma-separated list, nothing else
4. If no emails are found, return "NOT_FOUND"

Example output:
email1@example.com,email2@example.com,captain@example.com

Please extract ALL emails for team "{team_name}":"""
    
    def _parse_llm_response(self, response: str) -> Optional[List[str]]:
        """
        Parse the LLM response to extract email addresses.
        
        Args:
            response: Raw response from Ollama
            
        Returns:
            List of email addresses or None if not found
        """
        # Clean up the response
        response = response.strip()
        
        # Check for NOT_FOUND
        if response.upper() == "NOT_FOUND":
            return None
        
        # Split by comma and clean up each email
        emails = []
        for email in response.split(','):
            email = email.strip()
            if self._is_valid_email(email):
                emails.append(email)
        
        return emails if emails else None
    
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
    
    def get_all_team_contacts(self) -> Dict[str, List[str]]:
        """
        Extract all team contacts from the file.
        
        Returns:
            Dictionary mapping team names to lists of email addresses
        """
        contacts_content = self.load_contacts_file()
        if not contacts_content:
            return {}
        
        prompt = f"""You are a helpful assistant that extracts team names and their email addresses from contact information.

Given the following contacts file content, extract all team names and their associated email addresses.

Contacts file content:
{contacts_content}

Instructions:
1. Identify all team names in the content
2. For each team, find ALL their associated email addresses
3. Return the results in JSON format like this:
{{
    "Team Name 1": ["email1@example.com", "email2@example.com"],
    "Team Name 2": ["captain@example.com", "manager@example.com"]
}}

Please extract all team contacts:"""
        
        response = self._call_ollama(prompt)
        if not response:
            return {}
        
        try:
            # Try to parse as JSON
            contacts = json.loads(response)
            logger.info(f"Extracted contacts for {len(contacts)} teams")
            return contacts
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, trying alternative parsing")
            return self._parse_contacts_alternative(response)
    
    def _parse_contacts_alternative(self, response: str) -> Dict[str, List[str]]:
        """
        Alternative parsing method if JSON parsing fails.
        
        Args:
            response: Raw response from Ollama
            
        Returns:
            Dictionary mapping team names to lists of email addresses
        """
        contacts = {}
        
        # Look for patterns like "Team Name: email1@example.com, email2@example.com"
        import re
        lines = response.split('\n')
        
        current_team = None
        current_emails = []
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    team_part = parts[0].strip()
                    email_part = parts[1].strip()
                    
                    # Check if this looks like a team name (not just an email)
                    if not '@' in team_part and len(team_part) > 3:
                        # Save previous team if exists
                        if current_team and current_emails:
                            contacts[current_team] = current_emails
                        
                        # Start new team
                        current_team = team_part
                        current_emails = []
                        
                        # Extract emails from this line
                        emails = [e.strip() for e in email_part.split(',')]
                        for email in emails:
                            if self._is_valid_email(email):
                                current_emails.append(email)
                    else:
                        # This might be additional emails for current team
                        emails = [e.strip() for e in email_part.split(',')]
                        for email in emails:
                            if self._is_valid_email(email):
                                current_emails.append(email)
        
        # Save last team
        if current_team and current_emails:
            contacts[current_team] = current_emails
        
        return contacts
    
    def test_ollama_connection(self) -> bool:
        """
        Test if Ollama is running and accessible.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            models = response.json().get('models', [])
            available_models = [model['name'] for model in models]
            
            if self.model in available_models:
                logger.info(f"✅ Ollama is running and model '{self.model}' is available")
                return True
            else:
                logger.warning(f"⚠️ Ollama is running but model '{self.model}' not found")
                logger.info(f"Available models: {available_models}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            logger.error(f"❌ Error testing Ollama connection: {e}")
            return False 