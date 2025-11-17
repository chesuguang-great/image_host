# api delete
import os
from flask import Blueprint, request, jsonify
from utils.github_client import GitHubClient

delete_bp = Blueprint('delete', __name__)

IMAGE_PRE = 'images/'

@delete_bp.route('/delete', methods=['POST'])
def delete_image():
    filename = request.form['filename']

    if not filename:
        return jsonify('error', '需要提供文件名'), 400
    
    filepath = f'{IMAGE_PRE}{filename}'
    print(filepath)

    github_client = GitHubClient(
        os.environ.get('GITHUB_TOKEN'),
        os.environ.get('GITHUB_REPO')
    )

    try:
        github_client.delete_image(filepath)
        return jsonify({
            'success': True,
            'message': '删除成功'
        })
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500