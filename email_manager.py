"""
Email management module for Gmail API operations and email scheduling.
"""

import logging
import os
import base64
import email
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import config

logger = logging.getLogger(__name__)


class EmailManager:
    """Handles Gmail API operations and email scheduling."""
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Load existing token
        if os.path.exists(config.GMAIL_TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(
                    config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES
                )
                logger.info("Loaded existing Gmail credentials")
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Gmail credentials")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Generated new Gmail credentials")
                except Exception as e:
                    logger.error(f"Error generating credentials: {e}")
                    return
            
            # Save credentials for next run
            try:
                with open(config.GMAIL_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Saved Gmail credentials")
            except Exception as e:
                logger.error(f"Error saving credentials: {e}")
        
        # Build the Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail service initialized successfully")
        except Exception as e:
            logger.error(f"Error building Gmail service: {e}")
    
    def load_email_template(self) -> Optional[str]:
        """
        Load the HTML email template from file.
        
        Returns:
            Template content as string or None if failed
        """
        try:
            with open(config.EMAIL_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
                template = f.read()
            logger.info("Email template loaded successfully")
            return template
        except FileNotFoundError:
            logger.error(f"Email template file not found: {config.EMAIL_TEMPLATE_FILE}")
            return None
        except Exception as e:
            logger.error(f"Error loading email template: {e}")
            return None
    
    def _embed_map_image(self, html_content: str) -> str:
        """
        Embed the map image in the HTML content if available.
        
        Args:
            html_content: Original HTML content
            
        Returns:
            HTML content with embedded image
        """
        try:
            if os.path.exists(config.MAP_IMAGE_PATH):
                # Read and encode the image
                with open(config.MAP_IMAGE_PATH, 'rb') as f:
                    image_data = f.read()
                
                # Encode image as base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Get image MIME type based on file extension
                file_ext = os.path.splitext(config.MAP_IMAGE_PATH)[1].lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif'
                }.get(file_ext, 'image/jpeg')
                
                # Replace the map image placeholder with embedded image
                img_tag = f'<img src="data:{mime_type};base64,{image_base64}" alt="Cricket Pitch Location Map" style="max-width: 100%; height: auto; border-radius: 5px;" />'
                
                # Replace the map image src with embedded data
                html_content = html_content.replace(
                    'src="assets/cricket_pitch_map.jpg"',
                    f'src="data:{mime_type};base64,{image_base64}"'
                )
                
                logger.info("Map image embedded successfully")
            else:
                logger.warning(f"Map image not found: {config.MAP_IMAGE_PATH}")
                
        except Exception as e:
            logger.error(f"Error embedding map image: {e}")
        
        return html_content
    
    def _embed_team_logos(self, html_content: str, opponent_logo_url: str, sparta_logo_url: str) -> str:
        """
        Download and embed team logos as base64 data to ensure they display in emails.
        
        Args:
            html_content: Original HTML content
            opponent_logo_url: URL of opponent team logo
            sparta_logo_url: URL of SPARTA XI logo
            
        Returns:
            HTML content with embedded base64 images
        """
        try:
            import requests
            
            # Download and embed opponent logo
            if opponent_logo_url:
                try:
                    response = requests.get(opponent_logo_url, timeout=10)
                    if response.status_code == 200:
                        image_data = response.content
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        # Determine MIME type from URL
                        if opponent_logo_url.lower().endswith('.png'):
                            mime_type = 'image/png'
                        elif opponent_logo_url.lower().endswith('.jpeg') or opponent_logo_url.lower().endswith('.jpg'):
                            mime_type = 'image/jpeg'
                        else:
                            mime_type = 'image/jpeg'
                        
                        # Replace opponent logo placeholder with embedded base64
                        html_content = html_content.replace(
                            'src="{OPPONENT_LOGO}"',
                            f'src="data:{mime_type};base64,{image_base64}"'
                        )
                        logger.info("Opponent logo embedded successfully as base64")
                    else:
                        logger.warning(f"Failed to download opponent logo: {response.status_code}")
                        # Fallback to URL if download fails
                        html_content = html_content.replace(
                            'src="{OPPONENT_LOGO}"',
                            f'src="{opponent_logo_url}"'
                        )
                        logger.info("Using opponent logo URL as fallback")
                except Exception as e:
                    logger.error(f"Error downloading opponent logo: {e}")
                    # Fallback to URL if download fails
                    if opponent_logo_url:
                        html_content = html_content.replace(
                            'src="{OPPONENT_LOGO}"',
                            f'src="{opponent_logo_url}"'
                        )
                        logger.info("Using opponent logo URL as fallback")
            else:
                logger.warning("No opponent logo URL provided")
            
            # Download and embed SPARTA XI logo
            if sparta_logo_url:
                try:
                    response = requests.get(sparta_logo_url, timeout=10)
                    if response.status_code == 200:
                        image_data = response.content
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        
                        # Determine MIME type from URL
                        if sparta_logo_url.lower().endswith('.png'):
                            mime_type = 'image/png'
                        elif sparta_logo_url.lower().endswith('.jpeg') or sparta_logo_url.lower().endswith('.jpg'):
                            mime_type = 'image/jpeg'
                        else:
                            mime_type = 'image/jpeg'
                        
                        # Replace SPARTA logo placeholder with embedded base64
                        html_content = html_content.replace(
                            'src="{SPARTA_LOGO}"',
                            f'src="data:{mime_type};base64,{image_base64}"'
                        )
                        logger.info("SPARTA XI logo embedded successfully as base64")
                    else:
                        logger.warning(f"Failed to download SPARTA logo: {response.status_code}")
                        # Fallback to URL if download fails
                        html_content = html_content.replace(
                            'src="{SPARTA_LOGO}"',
                            f'src="{sparta_logo_url}"'
                        )
                        logger.info("Using SPARTA logo URL as fallback")
                except Exception as e:
                    logger.error(f"Error downloading SPARTA logo: {e}")
                    # Fallback to URL if download fails
                    if sparta_logo_url:
                        html_content = html_content.replace(
                            'src="{SPARTA_LOGO}"',
                            f'src="{sparta_logo_url}"'
                        )
                        logger.info("Using SPARTA logo URL as fallback")
            else:
                logger.warning("No SPARTA XI logo URL provided")
                    
        except Exception as e:
            logger.error(f"Error embedding team logos: {e}")
        
        return html_content
    
    def create_email_message(self, to_emails: List[str], cc_emails: List[str], 
                           subject: str, html_content: str) -> Dict:
        """
        Create a Gmail API message object.
        
        Args:
            to_emails: List of recipient email addresses
            cc_emails: List of CC email addresses
            subject: Email subject
            html_content: HTML content of the email
            
        Returns:
            Gmail API message object
        """
        message = MIMEMultipart('alternative')
        
        # Set recipients
        message['to'] = ', '.join(to_emails)
        if cc_emails:
            message['cc'] = ', '.join(cc_emails)
        
        message['subject'] = subject
        
        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    def save_email_as_draft(self, to_emails: List[str], cc_emails: List[str], 
                           subject: str, html_content: str) -> bool:
        """
        Save an email as a draft in Gmail.
        
        Args:
            to_emails: List of recipient email addresses
            cc_emails: List of CC email addresses
            subject: Email subject
            html_content: HTML content of the email
            
        Returns:
            True if successfully saved as draft, False otherwise
        """
        if not self.service:
            logger.error("Gmail service not initialized")
            return False
        
        try:
            # Create the message
            message = self.create_email_message(to_emails, cc_emails, subject, html_content)
            
            # Save as draft
            logger.info(f"Saving email as draft to {to_emails} (CC: {cc_emails})")
            
            # Create the draft
            draft = self.service.users().drafts().create(
                userId='me', body={'message': message}
            ).execute()
            
            logger.info(f"Email saved as draft successfully. Draft ID: {draft['id']}")
            return True
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving email as draft: {e}")
            return False
    
    def calculate_send_date(self, game_date: datetime) -> Optional[datetime]:
        """
        Calculate the Tuesday before the Sunday game at 7:00 PM ET.
        
        Args:
            game_date: Date of the Sunday game
            
        Returns:
            Date and time to send the email (Tuesday 7:00 PM ET)
        """
        try:
            # Calculate the Tuesday before the Sunday game
            # Sunday is weekday 6, Tuesday is weekday 1
            days_before = (game_date.weekday() - 1) % 7
            if days_before == 0:
                days_before = 7  # If game is on Tuesday, go back 7 days
            
            tuesday_date = game_date - timedelta(days=days_before)
            
            # Set time to 7:00 PM ET
            send_datetime = datetime.combine(
                tuesday_date, 
                config.EMAIL_SEND_TIME
            )
            
            logger.info(f"Calculated send date: {send_datetime} for game on {game_date}")
            return send_datetime
            
        except Exception as e:
            logger.error(f"Error calculating send date: {e}")
            return None
    
    def get_cc_emails(self) -> List[str]:
        """
        Get CC email addresses from configuration.
        
        Returns:
            List of CC email addresses
        """
        if not config.CC_EMAILS:
            return []
        
        # Split by comma and clean up
        cc_emails = [email.strip() for email in config.CC_EMAILS.split(',')]
        # Filter out empty strings
        cc_emails = [email for email in cc_emails if email]
        
        logger.info(f"CC emails configured: {cc_emails}")
        return cc_emails
    
    def draft_game_invitation(self, game_info: Dict, contact_emails: List[str]) -> bool:
        """
        Send a game invitation email for a specific match.
        
        Args:
            game_info: Dictionary containing game information
            contact_emails: List of email addresses for the opponent team
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Load email template
            template = self.load_email_template()
            if not template:
                return False
            
            # Prepare email content
            game_date = game_info['date']
            opponent_team = game_info['opponent']
            
            # Format date for display
            display_date = game_date.strftime(config.DISPLAY_DATE_FORMAT)
            
            # Replace placeholders in template
            email_content = template.replace('{DATE}', display_date)
            email_content = email_content.replace('{OPPONENT_TEAM}', opponent_team)
            email_content = email_content.replace('{MAP_LINK}', config.SPARTA_MAP_LINK)
            
            # Get team logo URLs
            opponent_logo = game_info.get('opponent_logo', '')
            sparta_logo = game_info.get('sparta_logo', '')
            
            # Embed team logos (download and embed as base64)
            email_content = self._embed_team_logos(email_content, opponent_logo, sparta_logo)
            
            # Embed map image if available
            email_content = self._embed_map_image(email_content)
            
            # Create subject line using the new format
            subject = config.EMAIL_SUBJECT_FORMAT.format(OPPONENT_TEAM=opponent_team)
            
            # Get CC emails
            cc_emails = self.get_cc_emails()
            
            # Calculate intended send date (Tuesday before the game) for reference
            intended_send_date = self.calculate_send_date(game_date)
            if not intended_send_date:
                return False
            
            # Save the email as draft
            success = self.save_email_as_draft(
                to_emails=contact_emails,
                cc_emails=cc_emails,
                subject=subject,
                html_content=email_content
            )
            
            if success:
                logger.info(f"Game invitation saved as draft for {opponent_team} (intended send date: {intended_send_date})")
                logger.info(f"Recipients: {contact_emails}")
                logger.info(f"CC: {cc_emails}")
                logger.info(f"Opponent logo: {opponent_logo}")
                logger.info(f"SPARTA logo: {sparta_logo}")
            else:
                logger.error(f"Failed to save game invitation as draft for {opponent_team}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending game invitation: {e}")
            return False 