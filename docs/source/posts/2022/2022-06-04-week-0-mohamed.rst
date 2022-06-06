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

Did I get stuck anywhere?
-------------------------
I got stuck trying to get the multithreading showManager to work.

What is coming up next?
-----------------------
TBD.