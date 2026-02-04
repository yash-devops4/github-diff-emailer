#!/usr/bin/env python3
"""
GitHub Commit Diff Email Notifier
Sends emails with code diffs similar to GitLab's format when commits are pushed to GitHub
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import sys
from html import escape

class GitHubDiffEmailer:
    def __init__(self, smtp_config):
        """
        Initialize with SMTP configuration
        smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'from_email': 'notifications@yourcompany.com',
            'to_email': 'general-git-commit@hotwax.co'
        }
        """
        self.smtp_config = smtp_config
    
    def get_commit_diff(self, repo_owner, repo_name, commit_sha, github_token=None):
        """Fetch commit details and diff from GitHub API"""
        headers = {'Accept': 'application/vnd.github.v3.diff'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        
        # Get commit details
        commit_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}'
        response = requests.get(commit_url, headers={'Authorization': f'token {github_token}'} if github_token else {})
        commit_data = response.json()
        
        # Get diff
        diff_response = requests.get(commit_url, headers=headers)
        diff_text = diff_response.text
        
        return commit_data, diff_text
    
    def format_diff_html(self, diff_text, max_lines=500):
        """Format diff text into HTML with GitLab-style coloring"""
        html_lines = ['<pre style="font-family: monospace; font-size: 12px; background-color: #f6f8fa; padding: 10px; overflow-x: auto;">']
        
        lines = diff_text.split('\n')[:max_lines]
        
        for line in lines:
            escaped_line = escape(line)
            
            if line.startswith('+++') or line.startswith('---'):
                # File headers
                html_lines.append(f'<span style="font-weight: bold; color: #000;">{escaped_line}</span>')
            elif line.startswith('+'):
                # Added lines
                html_lines.append(f'<span style="background-color: #d4edda; color: #155724; display: block;">{escaped_line}</span>')
            elif line.startswith('-'):
                # Removed lines
                html_lines.append(f'<span style="background-color: #f8d7da; color: #721c24; display: block;">{escaped_line}</span>')
            elif line.startswith('@@'):
                # Hunk headers
                html_lines.append(f'<span style="background-color: #e7f3ff; color: #0366d6; display: block;">{escaped_line}</span>')
            elif line.startswith('diff --git'):
                # Diff headers
                html_lines.append(f'<span style="font-weight: bold; color: #6a737d; display: block; margin-top: 10px;">{escaped_line}</span>')
            else:
                # Context lines
                html_lines.append(f'<span style="color: #24292e;">{escaped_line}</span>')
        
        if len(diff_text.split('\n')) > max_lines:
            html_lines.append(f'<span style="color: #6a737d; font-style: italic;">\n\n... (diff truncated, showing first {max_lines} lines)</span>')
        
        html_lines.append('</pre>')
        return '\n'.join(html_lines)
    
    def create_email_body(self, commit_data, diff_html, repo_url):
        """Create email body similar to GitLab format"""
        commit_info = commit_data.get('commit', {})
        author = commit_info.get('author', {})
        
        # Extract file changes
        files = commit_data.get('files', [])
        changed_paths = '\n'.join([f"  {'M' if f.get('status') == 'modified' else 'A' if f.get('status') == 'added' else 'D'} {f.get('filename')}" for f in files])
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #24292e; }}
                .header {{ background-color: #f6f8fa; padding: 15px; border-left: 4px solid #0366d6; margin-bottom: 20px; }}
                .info-section {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #586069; }}
                .commit-msg {{ font-style: italic; color: #24292e; padding: 10px; background-color: #f6f8fa; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h3 style="margin: 0; color: #0366d6;">New Commit Notification</h3>
            </div>
            
            <div class="info-section">
                <span class="label">Branch:</span> {commit_data.get('branch', 'N/A')}<br>
                <span class="label">Home:</span> <a href="{repo_url}">{repo_url}</a><br>
                <span class="label">Commit:</span> {commit_data.get('sha', '')[:12]}<br>
                <span style="margin-left: 20px;"><a href="{commit_data.get('html_url')}">{commit_data.get('html_url')}</a></span><br>
                <span class="label">Author:</span> {author.get('name', 'Unknown')} &lt;{author.get('email', '')}&gt;<br>
                <span class="label">Date:</span> {author.get('date', '')}
            </div>
            
            <div class="info-section">
                <span class="label">Changed paths:</span>
                <pre style="margin: 5px 0; padding: 10px; background-color: #f6f8fa;">{changed_paths}</pre>
            </div>
            
            <div class="info-section">
                <span class="label">Log Message:</span>
                <div class="commit-msg">
                -----------<br>
                {escape(commit_info.get('message', ''))}
                </div>
            </div>
            
            <hr style="border: 1px solid #e1e4e8; margin: 20px 0;">
            
            <div class="info-section">
                <span class="label">Changes:</span>
                {diff_html}
            </div>
            
            <hr style="border: 1px solid #e1e4e8; margin: 20px 0;">
            
            <p style="font-size: 11px; color: #6a737d;">
                To unsubscribe from these emails, change your notification settings at 
                <a href="{repo_url}/settings/notifications">{repo_url}/settings/notifications</a>
            </p>
        </body>
        </html>
        """
        
        return html_body
    
    def send_email(self, subject, html_body, text_body=None):
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.smtp_config['from_email']
        msg['To'] = self.smtp_config['to_email']
        
        # Add plain text version
        if text_body:
            part1 = MIMEText(text_body, 'plain')
            msg.attach(part1)
        
        # Add HTML version
        part2 = MIMEText(html_body, 'html')
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
    
    def process_webhook(self, webhook_data, github_token=None):
        """Process GitHub webhook payload and send email"""
        # Extract repository info
        repo = webhook_data.get('repository', {})
        repo_name = repo.get('name')
        repo_owner = repo.get('owner', {}).get('login')
        repo_url = repo.get('html_url')
        
        # Get commits from webhook
        commits = webhook_data.get('commits', [])
        ref = webhook_data.get('ref', '')
        branch = ref.split('/')[-1] if '/' in ref else ref
        
        for commit in commits:
            commit_sha = commit.get('id')
            
            # Fetch full commit details and diff
            commit_data, diff_text = self.get_commit_diff(
                repo_owner, repo_name, commit_sha, github_token
            )
            
            # Add branch info to commit data
            commit_data['branch'] = branch
            
            # Format diff as HTML
            diff_html = self.format_diff_html(diff_text)
            
            # Create email
            html_body = self.create_email_body(commit_data, diff_html, repo_url)
            
            # Email subject
            author_name = commit.get('author', {}).get('name', 'Unknown')
            subject = f"'{author_name}' via HC General Commit Notification List"
            
            # Send email
            self.send_email(subject, html_body)
            print(f"Email sent for commit {commit_sha[:12]}")


def main():
    """Example usage"""
    # Configuration
    smtp_config = {
        'server': 'smtp.gmail.com',
        'port': 587,
        'username': 'your-email@gmail.com',  # Update this
        'password': 'your-app-password',      # Update this (use app-specific password)
        'from_email': 'general-git-commit@hotwax.co',
        'to_email': 'general-git-commit@hotwax.co'
    }
    
    github_token = 'your_github_token_here'  # Update this
    
    # Example: Process a webhook (normally this comes from GitHub)
    # You would set up a Flask/FastAPI server to receive webhooks
    
    emailer = GitHubDiffEmailer(smtp_config)
    
    # Example webhook data structure
    example_webhook = {
        "ref": "refs/heads/refund-processing",
        "repository": {
            "name": "mantle-shopify-connector",
            "owner": {"login": "hotwax"},
            "html_url": "https://github.com/hotwax/mantle-shopify-connector"
        },
        "commits": [
            {
                "id": "f11d0c0937dbb35248a53b1ee5583eca90eb9cde",
                "message": "updated orders and returns services",
                "author": {
                    "name": "Prerak Ghatode",
                    "email": "prerakghatode4@gmail.com"
                }
            }
        ]
    }
    
    # Process webhook
    # emailer.process_webhook(example_webhook, github_token)


if __name__ == '__main__':
    main()
