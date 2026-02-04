#!/usr/bin/env python3
"""
GitHub Webhook Server
Receives GitHub push webhooks and sends formatted emails with diffs
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from github_diff_emailer import GitHubDiffEmailer
import json

app = Flask(__name__)

# Configuration - Load from environment variables
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', 587)),
    'username': os.getenv('SMTP_USERNAME'),
    'password': os.getenv('SMTP_PASSWORD'),
    'from_email': os.getenv('FROM_EMAIL', 'general-git-commit@hotwax.co'),
    'to_email': os.getenv('TO_EMAIL', 'general-git-commit@hotwax.co')
}

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')  # Optional: for webhook verification

emailer = GitHubDiffEmailer(SMTP_CONFIG)


def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature"""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret is set
    
    hash_object = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle GitHub push webhook"""
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature and not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Get event type
    event_type = request.headers.get('X-GitHub-Event')
    
    # Only process push events
    if event_type != 'push':
        return jsonify({'message': f'Ignored event type: {event_type}'}), 200
    
    # Parse webhook data
    webhook_data = request.json
    
    # Skip if no commits (like branch deletion)
    if not webhook_data.get('commits'):
        return jsonify({'message': 'No commits to process'}), 200
    
    try:
        # Process webhook and send emails
        emailer.process_webhook(webhook_data, GITHUB_TOKEN)
        return jsonify({'message': 'Emails sent successfully'}), 200
    
    except Exception as e:
        app.logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    # Run server
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
