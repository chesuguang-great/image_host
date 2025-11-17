# api/upload.py
from flask import Blueprint, request, jsonify
from utils.github_client import GitHubClient
from utils.image_utils import process_image
import os
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': '未提供图片文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    # 处理图片
    success, message, processed_image, new_filename = process_image(
        file.stream,
        file.filename,
        optimize=True
    )

    if not success:
        return jsonify({'error': message}), 400
    

    # 通过GitHub API上传
    github_client = GitHubClient(
        os.environ.get('GITHUB_TOKEN'),
        os.environ.get('GITHUB_REPO')
    )

    try:
        image_path = github_client.upload_image(processed_image.getvalue(), new_filename)
        image_url = f"https://{os.environ.get('CUSTOM_DOMAIN')}/{image_path}"

        return jsonify({
            'success': True,
            'url': image_url,
            'filename': new_filename
        })
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500