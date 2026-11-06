# Best Practices, Errors & Troubleshooting

## Best Practices

1. **Paper Indexing**
   - Index papers as soon as they're published on arXiv
   - Include full citation information in model/dataset cards
   - Use consistent paper references across related repositories

2. **Metadata Management**
   - Add YAML frontmatter to all model/dataset cards
   - Include proper licensing information
   - Tag with relevant task categories and domains

3. **Authorship**
   - Claim authorship on papers where you're listed as author
   - Use institutional email addresses for verification
   - Keep paper visibility settings updated

4. **Repository Linking**
   - Link papers to all relevant models, datasets, and Spaces
   - Include paper context in README descriptions
   - Add BibTeX citations for easy reference

5. **Research Articles**
   - Use templates consistently within projects
   - Include code and data links in papers
   - Generate web-friendly HTML versions for sharing

## Error Handling

- **Paper Not Found**: arXiv ID doesn't exist or isn't indexed yet
- **Permission Denied**: HF_TOKEN lacks write access to repository
- **Invalid YAML**: Malformed metadata in README frontmatter
- **Authorship Failed**: Email doesn't match paper author records
- **Already Claimed**: Another user has claimed authorship
- **Rate Limiting**: Too many API requests in short time

## Troubleshooting

**Issue**: "Paper not found on Hugging Face"
- **Solution**: Visit `hf.co/papers/{arxiv-id}` to trigger indexing

**Issue**: "Authorship claim not verified"
- **Solution**: Wait for admin review or contact HF support with proof

**Issue**: "arXiv tag not appearing"
- **Solution**: Ensure README includes proper arXiv URL format

**Issue**: "Cannot link to repository"
- **Solution**: Verify HF_TOKEN has write permissions

**Issue**: "Template rendering errors"
- **Solution**: Check markdown syntax and YAML frontmatter format

## Future Enhancements

Planned features for future versions:
- Support for non-arXiv papers (conference proceedings, journals)
- Automatic citation formatting from DOI
- Paper comparison and versioning tools
- Collaborative paper writing features
- Integration with LaTeX workflows
- Automated figure and table extraction
- Paper metrics and impact tracking
