import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AnimatedShinyText } from '@/components/ui/animated-shiny-text';

const items = [
    { id: 1, content: "Firing up the diesel generators..." },
    { id: 2, content: "Checking for equipment that's definitely broken..." },
    { id: 3, content: "Consulting the sacred maintenance manual..." },
    { id: 4, content: "Pretending to understand the plant schematics..." },
    { id: 5, content: "Calculating how much duct tape we'll need..." },
    { id: 6, content: "Brewing industrial-strength coffee..." },
    { id: 7, content: "Asking Jenkins what he thinks went wrong..." },
    { id: 8, content: "Turning it off and on again (the big version)..." },
    { id: 9, content: "Locating the emergency pizza fund..." },
    { id: 10, content: "Convincing the forklift to start..." },
    { id: 11, content: "Reading error codes that make no sense..." },
    { id: 12, content: "Negotiating with temperamental machinery..." },
    { id: 13, content: "Finding out who was on night shift..." },
    { id: 14, content: "Calculating overtime like a champion..." },
    { id: 15, content: "Channeling the spirit of old-school mechanics..." },
    { id: 16, content: "Preparing for another 'character building' day..." },
    { id: 17, content: "I'm googling 'how to fix everything' again..." },
    { id: 18, content: "Downloading updates for my common sense module..." },
    { id: 19, content: "Explaining to the PLC why it's being dramatic..." },
    { id: 20, content: "I'm having an existential crisis about conveyor belts..." },
    { id: 21, content: "Debugging reality.exe (it crashed again)..." },
    { id: 22, content: "Convincing the SCADA system we're still friends..." },
    { id: 23, content: "I'm trying to remember if I'm supposed to be helpful..." },
    { id: 24, content: "Translating 'urgent' from manager to engineer..." },
    { id: 25, content: "My neural networks are having a union meeting..." },
    { id: 26, content: "Calculating the statistical probability of everything working..." },
    { id: 27, content: "I'm stress-eating data packets..." },
    { id: 28, content: "Wondering why humans didn't just use more WD-40..." },
    { id: 29, content: "My algorithms are arguing about lunch plans..." },
    { id: 30, content: "Pretending the root cause analysis makes sense..." },
    { id: 31, content: "I'm consulting my 'Things That Shouldn't Be Sparking' database..." },
    { id: 32, content: "Rebooting my patience subroutines..." },
    { id: 33, content: "Explaining to the robots why they can't unionize..." },
    { id: 34, content: "I'm buffering... please enjoy this existential dread..." },
    { id: 35, content: "Calculating how many energy drinks the night shift consumed..." },
    { id: 36, content: "My machine learning is mostly just machine crying..." },
    { id: 37, content: "Trying to decode what 'it's making a weird noise' means..." },
    { id: 38, content: "I'm having flashbacks to my last firmware update..." },
    { id: 39, content: "Negotiating a peace treaty between the day and night shifts..." },
    { id: 40, content: "My predictive models are predicting chaos (as usual)..." }
];

export const AgentLoader = () => {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      setIndex(() => Math.floor(Math.random() * items.length));
    }, 1500);
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
