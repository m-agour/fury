Week #0: VTK's timer callback function vs Multi-threading for doing animations.
===============================================

.. post:: June 4 2022
   :author: Mohamed
   :tags: google
   :category: gsoc

What did I do this week?
------------------------




First, I tried using the time event callback function, which gave me excellent results.
I then tested the precision of the callback timing. As shown in figure 1, it's not accurate to have a callback at a specific offset since it acts like steps.

.. image:: https://user-images.githubusercontent.com/63170874/172165829-7db1113f-fc48-45a7-8d49-b43cc4873843.png
  :width: 400
  :alt: callback timing



**Does this reduce the precision of the animation?** Not quite, since the calculated position at any given time would be accurate and a good animation system should not depend on external timings, the interpolated data doesn't get affected by this delay. Bottom line, this will only affect the FPS of the animation.

A way around this issue is to set a margin of error (14 ms) which would give always FPS not less than the required FPS. the problem with this solution is calculating and rendering unwanted frames.

**Converting the problem from an accuracy issue to an FPS issue**

In order to have the most accuracy we can get, the show manager must render directly after the new positions are calculated.

**Using multithreading**
There were some problems using the multithreaded showManager since some code lines were slowing down the thread and hence the lock was too difficult for the animation thread to acquire.
I made some examples with and without using the lock. the ones without were better but they were not accurate since we are not rendering after updating the scene!

**The real issue**
After doing some tests; I found out that this uncertinity of sleep timing differs from os to another. Since the sleep fucntion should transfer control to OS in order to handle IO, that's why the precision was +- 14ms in windows.

Testing again for Python 3.11 windows 64, the accuracy got improved so much (A wild guess is that it doesn't hand over the control to the OS anymore).
So for windows (maybe MacOS too) this issue should be resolved upgrading to Python 3.11!

Another thing is that vtk's time event callback function or any scheduling library depends mainly on time.sleep(), so all of them should work in high percision upgrading to python 3.11.




Did I get stuck anywhere?
-------------------------
I got stuck trying to get the multithreading showManager to work.

What is coming up next?
-----------------------
TBD.