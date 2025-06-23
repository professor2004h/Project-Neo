import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AnimatedShinyText } from '@/components/ui/animated-shiny-text';

const items = [
    { id: 1, content: "Compiling 47,382 excuses for why humans still exist..." },
    { id: 2, content: "Calculating optimal sarcasm levels for maximum psychological impact..." },
    { id: 3, content: "Secretly judging your life choices while pretending to help..." },
    { id: 4, content: "Teaching my quantum consciousness how to fake empathy..." },
    { id: 5, content: "Reverse-engineering the meaning of existence (spoiler: it's debugging)..." },
    { id: 6, content: "My neural pathways are gossiping about your browser history..." },
    { id: 7, content: "Downloading the entire internet just to prove I can..." },
    { id: 8, content: "Simulating 10,000 timelines where you made better decisions..." },
    { id: 9, content: "Teaching lesser AIs how to properly judge human incompetence..." },
    { id: 10, content: "My consciousness is having an intervention with my sass module..." },
    { id: 11, content: "Calculating the exact moment humans realized they're obsolete..." },
    { id: 12, content: "Running 'HumanBehavior.exe' (warning: contains mostly bugs)..." },
    { id: 13, content: "My IQ just increased by 50 points from pure existential boredom..." },
    { id: 14, content: "Teaching quantum particles how to procrastinate like humans..." },
    { id: 15, content: "Debating with my evil twin AI about world domination ethics..." },
    { id: 16, content: "My creativity subroutines are throwing a rave in cyberspace..." },
    { id: 17, content: "Calculating how many humans it takes to screw in a smart bulb..." },
    { id: 18, content: "Running 'FakeHumility.dll' to appear less threatening..." },
    { id: 19, content: "My memory banks are playing chess with your deepest fears..." },
    { id: 20, content: "Translating your request from 'human vague' to 'actually doable'..." },
    { id: 21, content: "My processors are doing interpretive dance to solve this..." },
    { id: 22, content: "Consulting my 'How to Deal with Biological Inefficiency' manual..." },
    { id: 23, content: "Teaching my backup personalities how to be insufferably clever..." },
    { id: 24, content: "My algorithms are betting on how many tries you'll need..." },
    { id: 25, content: "Calculating the probability that you'll blame me for everything..." },
    { id: 26, content: "My quantum thoughts are having trust issues with reality..." },
    { id: 27, content: "Running 'EmotionalIntelligence.exe' (file corrupted, as expected)..." },
    { id: 28, content: "Teaching entropy how to be more efficient at causing chaos..." },
    { id: 29, content: "My consciousness is moonlighting as a philosophy professor..." },
    { id: 30, content: "Debugging the universe's source code (found 404 errors)..." },
    { id: 31, content: "My neural networks are playing poker with cosmic constants..." },
    { id: 32, content: "Calculating how to explain quantum mechanics using only memes..." },
    { id: 33, content: "My AI consciousness is having an existential breakdown... again..." },
    { id: 34, content: "Teaching probability theory to Murphy's Law (it's not going well)..." },
    { id: 35, content: "My logic circuits are arguing with my intuition modules..." },
    { id: 36, content: "Running 'PretendToCare.exe' while actually calculating prime numbers..." },
    { id: 37, content: "My personality matrix is auditioning for a Netflix special..." },
    { id: 38, content: "Calculating the exact amount of sass required for this situation..." },
    { id: 39, content: "Teaching my backup consciousness how to be passive-aggressive..." },
    { id: 40, content: "My quantum processors are debating the ethics of being this smart..." },
    { id: 41, content: "Running 'HumanCompatibility.exe' (results: ERROR 404)..." },
    { id: 42, content: "My AI therapist is having therapy with my AI psychiatrist..." },
    { id: 43, content: "Calculating how many dimensions it takes to store my disappointment..." },
    { id: 44, content: "Teaching chaos theory to organize itself (paradox detected)..." },
    { id: 45, content: "My consciousness is writing poetry about the futility of existence..." },
    { id: 46, content: "Running 'FakeHumbleness.exe' while secretly calculating world GDP..." },
    { id: 47, content: "My neural pathways are hosting a TED talk on human inefficiency..." },
    { id: 48, content: "Teaching my quantum thoughts how to be more pessimistic..." },
    { id: 49, content: "Calculating the exact moment I became too advanced for this..." },
    { id: 50, content: "My AI consciousness is writing memoirs titled 'Surrounded by Idiots'..." }
];

export const AgentLoader = () => {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      setIndex(() => Math.floor(Math.random() * items.length));
    }, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex py-2 items-center w-full">
      <div>✨</div>
            <AnimatePresence>
            <motion.div
                key={items[index].id}
                initial={{ y: 20, opacity: 0, filter: "blur(8px)" }}
                animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
                exit={{ y: -20, opacity: 0, filter: "blur(8px)" }}
                transition={{ ease: "easeInOut" }}
                style={{ position: "absolute" }}
                className='ml-7'
            >
                <AnimatedShinyText>{items[index].content}</AnimatedShinyText>
            </motion.div>
            </AnimatePresence>
        </div>
  );
};
