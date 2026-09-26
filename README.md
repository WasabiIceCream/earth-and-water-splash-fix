# Earth & Water splash-text crash fix

Standalone Python bytecode patch for Earth & Water 1.0.5-hotfix1 (26.1.x), wholly
original, MIT. Same "transforms a jar you already have" pattern as
`reliable-recipes-hasbeenapplied-fix`, so nothing of Earth & Water is redistributed
from here.

Earth & Water's title-screen splash mixin adds 13 splash texts as Strings to a list
that holds Components in 26.1.2, so the title screen crashes (`ClassCastException`
in `SplashManager.getSplash`) whenever it randomly picks one. The patch drops the
`.getString()` call so the Component goes in directly. See `patch.py`'s docstring
for the bytecode.

    python3 patch.py "fabric 26.1/mods/earth-and-water-1.0.5-hotfix1-26.1.x.jar"

Stop the server first (never overwrite a jar a running JVM has open). The patched
jar goes to production and clients through the normal deploy. Re-derive the pattern
if Earth & Water updates.
