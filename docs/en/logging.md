# Logging Guide

## Overview

The Gemini Media MCP Server provides detailed logging for all operations, including token usage tracking and cost estimation. This helps you monitor API usage and optimize your workflows.

## Log Format

All analysis tools use a structured logging format with clear visual indicators:

```
================================================================================
🎬 GIF ANALYSIS STARTED: /path/to/animation.gif
📊 Parameters: mode=total, quality=fhd, model=gemini-2.5-flash
🔧 Extraction: frame_count=5, gif_fps=None, interval_sec=None
✅ Extracted 5 frames from animation
💰 Token calculation:
  Frame 1 (1920x1080): 1,290 tokens
  Frame 2 (1920x1080): 1,290 tokens
  Frame 3 (1920x1080): 1,290 tokens
  Frame 4 (1920x1080): 1,290 tokens
  Frame 5 (1920x1080): 1,290 tokens
  Total: 6,450 tokens
💵 Estimated cost: $0.000121 USD (6,450 tokens @ gemini-2.5-flash)
🚀 Sending 5 frames to Gemini (gemini-2.5-flash)...
✅ Analysis completed successfully for /path/to/animation.gif
📈 Summary: 5 frames, 6,450 tokens, $0.000121 USD
================================================================================
```

## Icons Reference

| Icon | Meaning |
|------|---------|
| 🎬 | GIF analysis started |
| 🖼️ | Image analysis started |
| 🎵 | Audio analysis started |
| 📊 | Parameters used |
| 🔧 | Extraction settings |
| 📁 | File information |
| 🎧 | Audio format |
| ✅ | Success / Completion |
| 💰 | Token calculation |
| 💵 | Cost estimate |
| 🚀 | API request sent |
| 📈 | Summary statistics |
| ❌ | Error occurred |
| ⚠️ | Warning |

## Log Levels

### INFO

Standard operation logs showing:

- Operation start/completion
- Parameters and settings used
- Token counts and cost estimates
- Processing steps

### WARNING

Non-critical issues:

- Missing optional parameters
- Fallback to default settings
- Token calculation failures (non-blocking)

### ERROR

Critical failures:

- File not found
- Invalid formats
- API errors
- Parsing failures

## Token Usage Tracking

### Why Track Tokens?

Google Gemini API charges based on tokens processed. Tracking helps you:

- Monitor costs in real-time
- Optimize quality settings
- Plan batch operations
- Budget API usage

### Token Calculation

For images:

- Images ≤384px (both dimensions): 258 tokens
- Larger images: Tiled into 768px tiles
- Each tile: 258 tokens
- Formula: `(width_tiles × height_tiles) × 258`

Example:

- 1920×1080 image → 3×2 tiles = 6 tiles × 258 = 1,548 tokens
- 5 frames @ 1920×1080 → 7,740 tokens total

### Cost Estimation

Current Gemini pricing (as of 2024):

| Model | Input Price | Notes |
|-------|------------|-------|
| gemini-2.5-flash | $0.0000075 per 1K tokens | Fastest, cheapest |
| gemini-2.5-flash-8b | $0.00000375 per 1K tokens | Economy option |
| gemini-2.5-pro | $0.000375 per 1K tokens | Most accurate |

Example calculations:

```
5 GIF frames @ FHD (1920×1080):
  7,740 tokens × $0.0000075 = $0.00005805 USD

10 GIF frames @ UHD (3840×2160):
  77,400 tokens × $0.0000075 = $0.0005805 USD
```

## Quality Presets Impact

### GIF Analysis

| Quality | Max Dimension | Tokens per Frame (approx) | 5 Frames Cost |
|---------|---------------|---------------------------|---------------|
| economy | 1280 | 1,032 | $0.00004 |
| balanced | 1536 | 1,290 | $0.00005 |
| hd | 1920 | 1,548 | $0.00006 |
| fhd | 1920 | 1,548 | $0.00006 |
| uhd | 3840 | 6,192 | $0.00023 |

### Recommendations

**For quick previews:**

- Use `economy` or `balanced`
- Extract fewer frames (3-5)
- Use `gemini-2.5-flash-8b`

**For detailed analysis:**

- Use `fhd` or `uhd`
- Extract more frames (10-20)
- Use `gemini-2.5-flash` or `gemini-2.5-pro`

**For batch processing:**

- Monitor cumulative costs in logs
- Start with `balanced` quality
- Use `total` mode with fixed frame count

## Log Files

Logs are saved to `logs/` directory with timestamps:

```
logs/
  server_2024-01-15.log
  server_2024-01-16.log
```

## Example Log Sessions

### Successful GIF Analysis

```
2024-01-15 14:30:25 - INFO - ================================================================================
2024-01-15 14:30:25 - INFO - 🎬 GIF ANALYSIS STARTED: tutorial.gif
2024-01-15 14:30:25 - INFO - 📊 Parameters: mode=total, quality=fhd, model=gemini-2.5-flash
2024-01-15 14:30:25 - INFO - 🔧 Extraction: frame_count=5, gif_fps=None, interval_sec=None
2024-01-15 14:30:26 - INFO - ✅ Extracted 5 frames from animation
2024-01-15 14:30:26 - INFO - 💰 Token calculation:
2024-01-15 14:30:26 - INFO -   Frame 1 (1920x1080): 1,290 tokens
2024-01-15 14:30:26 - INFO -   Frame 2 (1920x1080): 1,290 tokens
2024-01-15 14:30:26 - INFO -   Frame 3 (1920x1080): 1,290 tokens
2024-01-15 14:30:26 - INFO -   Frame 4 (1920x1080): 1,290 tokens
2024-01-15 14:30:26 - INFO -   Frame 5 (1920x1080): 1,290 tokens
2024-01-15 14:30:26 - INFO -   Total: 6,450 tokens
2024-01-15 14:30:26 - INFO - 💵 Estimated cost: $0.000121 USD (6,450 tokens @ gemini-2.5-flash)
2024-01-15 14:30:26 - INFO - 🚀 Sending 5 frames to Gemini (gemini-2.5-flash)...
2024-01-15 14:30:28 - INFO - ✅ Analysis completed successfully for tutorial.gif
2024-01-15 14:30:28 - INFO - 📈 Summary: 5 frames, 6,450 tokens, $0.000121 USD
2024-01-15 14:30:28 - INFO - ================================================================================
```

### Image Analysis

```
2024-01-15 14:35:10 - INFO - ================================================================================
2024-01-15 14:35:10 - INFO - 🖼️  IMAGE ANALYSIS STARTED: photo.jpg
2024-01-15 14:35:10 - INFO - 📊 Parameters: model=gemini-2.5-flash, system_instruction=default
2024-01-15 14:35:10 - INFO - 💰 Token estimate: 1,548 tokens
2024-01-15 14:35:10 - INFO - 💵 Estimated cost: $0.000012 USD
2024-01-15 14:35:10 - INFO - 🚀 Sending request to Gemini (gemini-2.5-flash)...
2024-01-15 14:35:11 - INFO - ✅ Analysis completed successfully for photo.jpg
2024-01-15 14:35:11 - INFO - 📈 Summary: 1,548 tokens, $0.000012 USD
2024-01-15 14:35:11 - INFO - ================================================================================
```

### Audio Analysis

```
2024-01-15 14:40:00 - INFO - ================================================================================
2024-01-15 14:40:00 - INFO - 🎵 AUDIO ANALYSIS STARTED: podcast.mp3
2024-01-15 14:40:00 - INFO - 📁 File size: 5.23 MB
2024-01-15 14:40:00 - INFO - 🎧 Format: audio/mpeg
2024-01-15 14:40:00 - INFO - 📊 Parameters: model=gemini-2.5-flash, system_instruction=default
2024-01-15 14:40:00 - INFO - 🚀 Sending 5.23 MB audio to Gemini (gemini-2.5-flash)...
2024-01-15 14:40:05 - INFO - ✅ Audio analysis completed successfully for podcast.mp3
2024-01-15 14:40:05 - INFO - 📈 Summary: 5.23 MB audio processed with gemini-2.5-flash
2024-01-15 14:40:05 - INFO - ================================================================================
```

## Troubleshooting Logs

### High Token Usage

```
⚠️  High token count detected: 77,400 tokens
Consider:
- Reducing quality preset (uhd → fhd → balanced)
- Extracting fewer frames
- Using lower resolution source
```

### Token Calculation Failure

```
⚠️  Could not calculate tokens: PIL Image error
Continuing without cost estimate...
```

This is non-blocking - analysis continues but without cost preview.

## Best Practices

1. **Monitor cumulative costs** - Check logs after batch operations
2. **Start small** - Test with `economy` quality first
3. **Use appropriate models** - Don't use `pro` for simple tasks
4. **Review summaries** - Check `📈 Summary` lines for quick stats
5. **Archive logs** - Rotate log files monthly for historical tracking

## Cost Control Tips

### Daily Budget Tracking

```bash
# Extract daily costs from logs
grep "📈 Summary" logs/server_$(date +%Y-%m-%d).log | \
  awk '{sum += $NF} END {print "Total: $" sum}'
```

### Frame Count Optimization

```python
# For a 30-second GIF at 24fps:
# Full: 720 frames × 1,548 tokens = 1,114,560 tokens ($8.36)
# 1 FPS: 30 frames × 1,548 tokens = 46,440 tokens ($0.35)
# 5 frames: 5 frames × 1,548 tokens = 7,740 tokens ($0.06)
```

Choose the minimum frames needed for your use case!

## Additional Resources

- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Token Calculation Details](https://ai.google.dev/gemini-api/docs/vision#prompting-with-images)
- [MCP Server Configuration](configuration.md)
