import re


class WebColorConverter:
    """专为Web开发优化的颜色转换器"""

    @staticmethod
    def normalize_rgb_values(r, g, b):
        """规范化RGB值到0-255范围"""
        if isinstance(r, float) and max(r, g, b) <= 1.0:
            # 如果是归一化值，转换为0-255
            return int(r * 255), int(g * 255), int(b * 255)
        return int(r), int(g), int(b)

    @staticmethod
    def validate_hex_color(hex_color):
        """验证HEX颜色格式"""
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return bool(re.match(pattern, hex_color))

    @staticmethod
    def hex_to_rgb(hex_color):
        """HEX转RGB"""
        if not WebColorConverter.validate_hex_color(hex_color):
            raise ValueError("无效的HEX颜色格式")

        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            # 简写形式 #RGB
            hex_color = ''.join([c * 2 for c in hex_color])

        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(r, g, b):
        """RGB转HEX"""
        r, g, b = WebColorConverter.normalize_rgb_values(r, g, b)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def rgb_to_hsl(r, g, b):
        """RGB转HSL"""
        import colorsys
        r, g, b = WebColorConverter.normalize_rgb_values(r, g, b)
        r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        return (int(h * 360), int(s * 100), int(l * 100))

    @staticmethod
    def hsl_to_rgb(h, s, l):
        """HSL转RGB"""
        import colorsys
        h_norm, s_norm, l_norm = h / 360, s / 100, l / 100
        r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
        return (int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def argb_to_hex(a, r, g, b):
        """ARGB转HEX（带Alpha通道）"""
        # 规范化所有值到0-255范围
        if isinstance(a, float) and a <= 1.0:
            a = int(a * 255)
        if isinstance(r, float) and r <= 1.0:
            r = int(r * 255)
        if isinstance(g, float) and g <= 1.0:
            g = int(g * 255)
        if isinstance(b, float) and b <= 1.0:
            b = int(b * 255)

        a, r, g, b = int(a), int(r), int(g), int(b)
        return f"#{a:02x}{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def hex_to_argb(hex_color):
        """HEX转ARGB（解析Alpha通道）"""
        if not isinstance(hex_color, str):
            raise ValueError("HEX颜色必须是字符串格式")

        hex_color = hex_color.lstrip('#')
        if len(hex_color) not in [6, 8]:
            raise ValueError("无效的HEX颜色格式")

        if len(hex_color) == 6:
            # 标准RGB格式，透明度默认为不透明(255)
            r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
            return 255, r, g, b
        else:
            # ARGB格式，包含透明度
            a, r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4, 6))
            return a, r, g, b

    @staticmethod
    def argb_to_int(a, r, g, b):
        """将ARGB值转换为整数表示形式"""
        if isinstance(a, float) and a <= 1.0:
            a = int(a * 255)
        if isinstance(r, float) and r <= 1.0:
            r = int(r * 255)
        if isinstance(g, float) and g <= 1.0:
            g = int(g * 255)
        if isinstance(b, float) and b <= 1.0:
            b = int(b * 255)

        a, r, g, b = int(a), int(r), int(g), int(b)
        return (a << 24) | (r << 16) | (g << 8) | b

    @staticmethod
    def int_to_argb(color_int):
        """将整数颜色值转换为ARGB元组"""
        a = (color_int >> 24) & 0xFF
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        return a, r, g, b
