from github import Github
import base64

class GitHubClient:
    def __init__(self, token, repo_name):
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)
    
    def upload_image(self, image_data, filename):
        # 编码图片数据
        content_base64 = base64.b64encode(image_data).decode()
        # 上传到GitHub
        self.repo.create_file(
            f"images/{filename}", 
            f"Add image: {filename}", 
            content_base64,
            branch="main"
        )
        return f"images/{filename}"
    
    def delete_image(self, filepath):
        # 获取文件SHA值
        contents = self.repo.get_contents(filepath)
        self.repo.delete_file(
            filepath, 
            f"Remove image: {filepath}", 
            contents.sha
        )