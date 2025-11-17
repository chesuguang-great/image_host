from github import Github
import base64

class GitHubClient:
    def __init__(self, token, repo_name):
        self.g = Github(token)
        self.repo = self.g.get_repo(repo_name)
    
    def upload_image(self, image_binary_data, filename):
        # 上传到GitHub
        self.repo.create_file(
            f"images/{filename}", 
            f"Add image: {filename}", 
            image_binary_data,
            branch="images-branch"
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