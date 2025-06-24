from django import forms
from django.utils.safestring import mark_safe


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': True})
        self.attrs = attrs

    def value_from_datadict(self, data, files, name):
        upload = files.getlist(name)
        if not upload:
            return None
        return upload


class MultipleImagePreviewWidget(forms.Widget):
    """
    A widget that shows existing images and allows uploading multiple new ones
    """
    template_name = 'admin/widgets/multiple_image_preview.html'
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        
    def format_value(self, value):
        if value is None:
            return []
        if hasattr(value, '__iter__'):
            return list(value)
        return [value]
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': True, 'accept': 'image/*'})
        
        html = f'''
        <div class="multiple-image-upload">
            <div class="current-images" id="current-images-{name}">
                <h4>Current Images:</h4>
                <div class="image-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px;">
                    <!-- Current images will be populated by JavaScript -->
                </div>
            </div>
            
            <div class="new-images-section">
                <h4>Upload New Images:</h4>
                <input type="file" name="{name}" multiple accept="image/*" 
                       style="margin-bottom: 10px;" onchange="previewNewImages(this, '{name}')">
                <div class="help-text" style="font-size: 11px; color: #666;">
                    Hold Ctrl/Cmd to select multiple images at once. Supported formats: JPG, PNG, GIF, WebP
                </div>
                
                <div id="new-images-preview-{name}" class="new-images-preview" 
                     style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin-top: 15px;">
                    <!-- New image previews will appear here -->
                </div>
            </div>
        </div>
        
        <style>
            .image-item {{
                position: relative;
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: hidden;
                background: #f9f9f9;
            }}
            .image-item img {{
                width: 100%;
                height: 120px;
                object-fit: cover;
                display: block;
            }}
            .image-item .image-info {{
                padding: 8px;
                font-size: 11px;
                background: white;
                border-top: 1px solid #eee;
            }}
            .image-item .primary-badge {{
                position: absolute;
                top: 5px;
                right: 5px;
                background: #28a745;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }}
            .remove-image {{
                position: absolute;
                top: 5px;
                left: 5px;
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                font-size: 12px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
        </style>
        
        <script>
            function previewNewImages(input, fieldName) {{
                const previewContainer = document.getElementById('new-images-preview-' + fieldName);
                previewContainer.innerHTML = '';
                
                if (input.files) {{
                    Array.from(input.files).forEach((file, index) => {{
                        if (file.type.startsWith('image/')) {{
                            const reader = new FileReader();
                            reader.onload = function(e) {{
                                const imageItem = document.createElement('div');
                                imageItem.className = 'image-item';
                                imageItem.innerHTML = `
                                    <img src="${{e.target.result}}" alt="Preview">
                                    <div class="image-info">
                                        <div><strong>${{file.name}}</strong></div>
                                        <div>Size: ${{(file.size / 1024 / 1024).toFixed(2)}} MB</div>
                                        <div>Type: ${{file.type}}</div>
                                    </div>
                                `;
                                previewContainer.appendChild(imageItem);
                            }};
                            reader.readAsDataURL(file);
                        }}
                    }});
                    
                    // Show count
                    const countDiv = document.createElement('div');
                    countDiv.style.cssText = 'margin-top: 10px; font-weight: bold; color: #28a745;';
                    countDiv.textContent = `${{input.files.length}} image(s) selected for upload`;
                    previewContainer.appendChild(countDiv);
                }}
            }}
            
            // Load current images when page loads
            document.addEventListener('DOMContentLoaded', function() {{
                // This would be populated from the backend if editing existing property
                // For now, it's just a placeholder
            }});
        </script>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        upload = files.getlist(name)
        if not upload:
            return None
        return upload