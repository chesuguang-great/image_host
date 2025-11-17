import os
import io
from PIL import Image, ImageFile
import magic
from datetime import datetime
import secrets
import string

# 处理截断的图片文件
ImageFile.LOAD_TRUNCATED_IMAGES = True

class ImageProcessor:
    """
    图片处理工具类，负责图片验证、格式转换和优化
    """
    
    # 允许的图片格式和对应的MIME类型
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/png', 
        'image/gif',
        'image/bmp',
        'image/webp'
    }
    
    # 格式转换映射（统一转换为目标格式）
    FORMAT_MAPPING = {
        'jpeg': 'JPEG',
        'jpg': 'JPEG', 
        'png': 'PNG',
        'webp': 'WEBP'
    }
    
    def __init__(self, max_size_mb=5, target_format='JPEG', quality=85):
        """
        初始化图片处理器
        
        Args:
            max_size_mb: 最大允许的图片大小(MB)
            target_format: 目标统一格式
            quality: JPEG/WEBP格式的压缩质量(1-100)
        """
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节
        self.target_format = target_format
        self.quality = quality
    
    def allowed_file(self, filename, file_stream=None):
        """
        验证文件类型是否允许上传[1,3](@ref)
        
        Args:
            filename: 文件名
            file_stream: 文件流(可选，用于MIME类型验证)
            
        Returns:
            bool: 是否允许上传
        """
        # 检查文件扩展名
        if '.' not in filename:
            return False
            
        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            return False
        
        # 如果提供了文件流，进行MIME类型验证
        if file_stream and hasattr(file_stream, 'read'):
            try:
                # 保存当前位置
                current_pos = file_stream.tell()
                file_stream.seek(0)
                
                # 使用python-magic验证真实的MIME类型
                mime_type = magic.from_buffer(file_stream.read(2048), mime=True)
                file_stream.seek(current_pos)  # 恢复位置
                
                if mime_type not in self.ALLOWED_MIME_TYPES:
                    return False
                    
            except Exception:
                # 如果magic检查失败，回退到扩展名检查
                pass
                
        return True
    
    def validate_image(self, file_stream):
        """
        验证图片文件的完整性和有效性[5](@ref)
        
        Args:
            file_stream: 文件流
            
        Returns:
            tuple: (success, message, image_object)
        """
        try:
            # 检查文件大小
            if hasattr(file_stream, 'seek') and hasattr(file_stream, 'tell'):
                current_pos = file_stream.tell()
                file_stream.seek(0, 2)  # 移动到末尾
                file_size = file_stream.tell()
                file_stream.seek(current_pos)  # 恢复位置
                
                if file_size > self.max_size:
                    return False, f"文件大小超过限制({self.max_size//1024//1024}MB)", None
            
            # 尝试用Pillow打开图片验证完整性
            try:
                image = Image.open(file_stream)
                image.verify()  # 验证图片完整性
            except Exception as e:
                return False, f"图片文件损坏或格式不支持: {str(e)}", None
            
            # 重新打开图片用于处理（verify()后需要重新打开）
            file_stream.seek(0)
            image = Image.open(file_stream)
            
            return True, "验证成功", image
            
        except Exception as e:
            return False, f"图片验证失败: {str(e)}", None
    
    def unify_image_format(self, image, target_format=None):
        """
        统一图片格式并优化[1,7,8](@ref)
        
        Args:
            image: PIL Image对象
            target_format: 目标格式，默认为初始化时设置的格式
            
        Returns:
            PIL Image对象: 处理后的图片
        """
        if target_format is None:
            target_format = self.target_format
        
        # 转换颜色模式（针对JPEG格式）
        if target_format.upper() == 'JPEG':
            if image.mode in ('RGBA', 'P', 'LA'):
                # 创建白色背景来处理透明通道
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
        
        return image
    
    def optimize_image(self, image, max_dimension=2048):
        """
        优化图片大小和质量[3,5](@ref)
        
        Args:
            image: PIL Image对象
            max_dimension: 最大边长（保持宽高比）
            
        Returns:
            PIL Image对象: 优化后的图片
        """
        # 计算缩放比例（保持宽高比）
        width, height = image.size
        if max(width, height) > max_dimension:
            ratio = max_dimension / max(width, height)
            new_size = (int(width * ratio), int(height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def process_image(self, file_stream, filename, optimize=True):
        """
        完整的图片处理流程：验证 → 优化 → 格式统一[8](@ref)
        
        Args:
            file_stream: 文件流
            filename: 原文件名
            optimize: 是否进行优化
            
        Returns:
            tuple: (success, message, processed_image_data, new_filename)
        """
        try:
            # 1. 验证文件类型
            if not self.allowed_file(filename, file_stream):
                return False, "不支持的文件格式", None, None
            
            # 2. 验证图片完整性
            success, message, image = self.validate_image(file_stream)
            if not success:
                return False, message, None, None
            
            # 3. 优化图片（如果需要）
            if optimize:
                image = self.optimize_image(image)
            
            # 4. 统一图片格式
            image = self.unify_image_format(image)
            
            # 5. 转换为字节数据
            output_buffer = io.BytesIO()
            save_args = {'format': self.target_format}
            
            # 设置质量参数（针对有损格式）
            if self.target_format in ['JPEG', 'WEBP']:
                save_args['quality'] = self.quality
                if self.target_format == 'WEBP':
                    save_args['method'] = 6  # 更好的压缩
            
            image.save(output_buffer, **save_args)
            output_buffer.seek(0)
            
            # 6. 生成新文件名
            new_filename = self.generate_filename(self.target_format.lower())
            
            return True, "图片处理成功", output_buffer.getvalue(), new_filename
            
        except Exception as e:
            return False, f"图片处理失败: {str(e)}", None, None
    
    def generate_filename(self, extension=None):
        """
        生成唯一的文件名[1](@ref)
        
        Args:
            extension: 文件扩展名
            
        Returns:
            str: 新文件名
        """
        if extension is None:
            extension = self.target_format.lower()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        
        return f"{timestamp}_{random_str}.{extension}"
    
    def get_image_info(self, image):
        """
        获取图片信息[5](@ref)
        
        Args:
            image: PIL Image对象
            
        Returns:
            dict: 图片信息
        """
        return {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height
        }


# 全局默认处理器实例
default_processor = ImageProcessor()

# 便捷函数
def allowed_file(filename, file_stream=None):
    """便捷函数：检查文件是否允许上传"""
    return default_processor.allowed_file(filename, file_stream)

def process_image(file_stream, filename, optimize=True):
    """便捷函数：处理图片"""
    return default_processor.process_image(file_stream, filename, optimize)

def validate_image(file_stream):
    """便捷函数：验证图片"""
    return default_processor.validate_image(file_stream)