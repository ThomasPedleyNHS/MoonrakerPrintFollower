#version 440
layout(location=0) in vec2 position;
layout(location=1) in vec2 direction;
layout(location=2) in vec2 corner;
layout(location=3) in vec2 motion;
layout(location=0) out vec2 localPos;
layout(location=1) out float segmentLength;
layout(location=2) flat out float visibleSegment;
layout(location=3) flat out float halfWidth;
layout(std140,binding=0) uniform buf { mat4 matrix; vec4 colour; vec4 parameters; vec4 options; } ubuf;
void main() {
    float amount = ubuf.options.z > 0.5 ? clamp((ubuf.options.y - motion.x) / max(motion.y,0.000001),0.0,1.0) : 1.0;
    visibleSegment = amount;
    vec2 shortened = direction * amount;
    vec2 point = position - (corner.x > 0.0 ? direction - shortened : vec2(0));
    vec4 anchor = ubuf.matrix * vec4(point,0,1);
    vec4 other = ubuf.matrix * vec4(point + shortened,0,1);
    vec2 delta = (other.xy / other.w - anchor.xy / anchor.w) * ubuf.parameters.yz;
    segmentLength = length(delta);
    vec2 tangent = segmentLength > 0.0001 ? delta / segmentLength : vec2(1,0);
    vec2 normal = vec2(-tangent.y,tangent.x);
    halfWidth = ubuf.parameters.x * (ubuf.options.w > 0.5 ? abs(corner.x) : 1.0);
    float endSign = sign(corner.x);
    float radius = halfWidth + (ubuf.parameters.w > 0.5 ? 1.0 : 0.0);
    vec2 offset = (tangent * endSign + normal * corner.y) * radius;
    gl_Position = anchor + vec4(offset / ubuf.parameters.yz * anchor.w,0,0);
    localPos = vec2((corner.x < 0 ? 0 : segmentLength) + endSign*radius, corner.y*radius);
}
