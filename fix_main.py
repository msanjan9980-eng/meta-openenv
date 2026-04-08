content = open('server/app.py', encoding='utf-8').read()

# Cut everything from the first 'def main' onwards and replace cleanly
cut_at = content.find('\ndef main(')
if cut_at == -1:
    cut_at = content.find('\n# FIX:')
top = content[:cut_at].rstrip()

bottom = '''

# Entry point — port 7860 matches HF Spaces requirement
def main(host: str = "0.0.0.0", port: int = 7860) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
'''

final = top + bottom
open('server/app.py', 'w', encoding='utf-8').write(final)
lines = final.splitlines()
print('\n'.join(lines[-10:]))
print('Done')