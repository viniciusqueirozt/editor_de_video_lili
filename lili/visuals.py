"""RGB grading matching the preview SVG: affine channels, then saturation."""
def color_filter(clip):
    brightness, contrast, saturation = (clip.get(k, 1) for k in ("brightness", "contrast", "saturation"))
    if (brightness, contrast, saturation) == (1, 1, 1): return ""
    slope = brightness * contrast
    offset = .5 * (1-contrast) * brightness * 255
    channel = f"clip(val*{slope}+({offset}),0,255)"
    luma = (.2126, .7152, .0722)
    matrix = [[luma[j]*(1-saturation)+(saturation if i==j else 0) for j in range(3)] for i in range(3)]
    coefficients = ":".join(f"{a}{b}={matrix[i][j]}" for i,a in enumerate("rgb") for j,b in enumerate("rgb"))
    return f"format=gbrp,lutrgb=r='{channel}':g='{channel}':b='{channel}',colorchannelmixer={coefficients}"


def tempo_filters(speed):
    factors = []
    while speed < .5:
        factors.append(.5); speed /= .5
    while speed > 2:
        factors.append(2); speed /= 2
    if speed != 1: factors.append(speed)
    return [f"atempo={factor}" for factor in factors]
