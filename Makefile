.PHONY: demo table
demo:                 ## guided step-through — the recommended first run
	@python3 demo.py
table:                ## just the three verdicts, no narration
	@python3 demo.py --table
