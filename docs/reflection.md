# Reflection

A learning project: a payment reconciliation checker built with AI assistants, using made-up data only.

## What I did and what the AI did
I wrote the original user stories and test cases, drew the process map, reviewed the output, and aligned the README and documents with each other. Claude refined my stories and test cases, generated the sample data and the Python script, and drafted the README. It also reformatted my final documents into Markdown for this repo. A second tool, Gemini, was used as an independent reviewer of the code and stories, and it raised the issues in the defect log. I worked through those with Claude and decided how each one was resolved. I did not write the code, and I did not find the defects myself.

## Where we disagreed, and what the AI got wrong
- **Scope.** The AI questioned how much Story 7 (the summary report) could do, and suggested a more thorough set of test cases, including payments made after the fifth failed retry (TC12). I chose to leave the fifth-failure case out and list it as a limit, because of limited time and no real data to test it against.
- **Assumptions about the process.** The clashes mostly came from information I had left out. The AI filled the gaps with its own assumptions about how billing works, and some were wrong. For example, it assumed the CRM would hold failed attempts. I corrected it: the CRM records successful payments only, so the gateway needed its own subscription link. Each time I clarified the rules so the stories matched the real process. The lesson is that the gaps in my own information hurt the work as much as the AI's assumptions did.
- **Code.** The Status Conflict check was incomplete (it checked the gateway status but not the CRM status), and the catch-up lookup links through the payment ID rather than the subscription ID. Both are in the defect log.

## Testing
All 12 test cases passed on the first run. That was weaker evidence than it looks, because the AI wrote both the code and the data. The cross-check with Gemini found issues that my review with Claude had not, so using a second AI as an independent reviewer worked better than relying on one. It is still AI checking AI. I made the decisions on each issue, but I'm not claiming deep testing skill. See `defect_log.md`.

## What I understood, and what I didn't
Given / When / Then, parameters and defect severity were new to me, because I haven't used them in my line of work. My own experience shaped the business rules, such as the grace period and the $300 refund limit, which helped me write more detailed stories.

I understand the logic of the missing-details and duplicate checks. I would need a day or two to prepare before explaining them line by line. I have a C++ background but limited Python, so reading the code is the hardest part for me.

## Time
It took well over the planned 8 hours. I worked on it in my spare time, and I had little experience with testing and finding defects.

## What I'd change next
- Test on larger data that is closer to real data.
- Cover the fifth-failure case properly.
- Improve duplicate detection so it accounts for one customer with two subscriptions.
- Save account-level results to a file.
- Give the AI more complete information about the process at the start.

## What I can and can't claim
I can claim writing user stories, setting up test scenarios, understanding the reconciliation process, process mapping, and a foundation in working with AI assistants, including using a second AI to cross-check the first. I can't claim the ability to write the code or optimise test cases.
