# Reference solution

The finished lab: exactly what your folder looks like at the end of Milestone 3. Try it yourself first!

To run it, follow the lab's *Before you start* steps, copy `.env` into this folder, set your name in `environments/travel-env.yaml`, then:

```bash
ant apply agents/travel-agent.md environments/travel-env.yaml skills/points-estimator
python make_vault.py
python chat.py
```
