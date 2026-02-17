from flask import Blueprint, request, jsonify
import hmac
import hashlib
import subprocess
import os

webhook_bp = Blueprint('webhook', __name__)

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-key-here')

@webhook_bp.route('/webhook/deploy', methods=['POST'])
def deploy():
    # Verify GitHub signature
    signature = request.headers.get('X-Hub-Signature-256')
    if signature:
        mac = hmac.new(
            WEBHOOK_SECRET.encode(),
            msg=request.data,
            digestmod=hashlib.sha256
        )
        expected = 'sha256=' + mac.hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({'error': 'Invalid signature'}), 403
    
    # Run deployment script
    subprocess.Popen(['/var/www/deploy-skyjo.sh'])
    return jsonify({'status': 'Deployment started'}), 200
