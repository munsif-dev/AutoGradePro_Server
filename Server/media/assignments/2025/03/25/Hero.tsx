"use client";
import React from "react";
import Link from "next/link";
import Image from "next/image";
import AnimatedText from "./AnimatedText";
import { motion } from "framer-motion";
import { Scale } from "lucide-react";

const Hero = () => {
  return (
    <>
      <div className="flex items-center justify-between w-full">
        <motion.div
          className="w-1/2 flex items-center justify-center mt-10 pr-8"
          whileHover={{ scale: 1.04, rotate: "0.5deg" }}
          whileTap={{ scale: 0.95, rotate: "-1deg" }}
          transition={{ duration: 0.125, ease: "easeInOut" }}
        >
          <Image
            width={526}
            height={576}
            alt="Hero Image"
            src="/Hero_Image.png"
          />
        </motion.div>
        <div className="w-1/2 flex flex-col  space-y-3">
          <AnimatedText
            type="h1"
            text="Transforming Grading Into a Breeze!"
            className="w-[845px]  text-[#894799] text-[80px] font-bold  leading-[90px] "
          />
          <p className="w-[600px]  text-[#894799] text-lg font-medium font-['Poppins'] leading-[30px]">
            {`"Let's make grading more organized and effortless with our
            streamlined platform, featuring the latest tools for efficient
            assessment."`}
          </p>

          <div className="flex items-center self-start">
            <Link
              href="/grading"
              target={"_blank"}
              className="flex items-center bg-light-2 text-pink-50 py-2 px-6 rounded-lg 
                  text-lg border-2 border-solid border-red font-semibold mr-4
                   hover:bg-light-3 hover:text-dark-1  hover:border-dark-2"
            >
              Get Started
            </Link>
            <Link
              href="https://youtu.be/9Gv2Xtb9NGc"
              target={"_blank"}
              className="ml-4 text-lg font-medium capitalize text-light-2 underline"
            >
              View Demo
            </Link>
          </div>
        </div>
      </div>
      {/* <div className="w-full flex justify-center items-center">
        <div className="w-[1266px] h-[520px] relative">
          <div className="w-[845px] h-[583px] left-0 top-[34px] absolute">
            <div className="w-[845px] left-0 top-0 absolute text-[#894799] text-[80px] font-bold  leading-[90px]">
              Transforming Grading Into a Breeze!
            </div>
            <div className="w-[600px] left-0 top-[330px] absolute text-[#894799] text-lg font-medium font-['Poppins'] leading-[30px]">
              "Let's make grading more organized and effortless with our
              streamlined platform, featuring the latest tools for efficient
              assessment."
            </div>
            <div className="h-[67px] px-[30px] py-5 left-0 top-[460px] absolute bg-[#894799] rounded-[40px] justify-center items-center gap-2.5 inline-flex">
              <div className="text-white text-lg font-medium font-['Poppins']">
                Click to Get Started
              </div>
            </div>
            <div className="w-[168.54px] h-10 left-[276.86px] top-[470px] absolute">
              <div className="w-[45.86px] h-10 px-[4.78px] py-[4.17px] left-0 top-0 absolute justify-center items-center inline-flex">
                <div className="w-[36.31px] h-[31.67px] relative"></div>
              </div>
              <div className="w-[112.36px] left-[56.18px] top-[9px] absolute text-[#191a15] text-lg font-medium font-['Poppins']">
                View Demo
              </div>
            </div>
          </div>
          <div className="w-[576px] h-[626px] left-[690px] top-0 absolute flex-col justify-center items-center inline-flex">
            <img className="w-[526px] h-[576px]" src="Hero_Image.png" />
          </div>
        </div>
      </div> */}
      <div className="w-full flex justify-center items-center mt-20 pt-16 ">
        <div className="w-[1194px] h-[162px] relative">
          <div className="left-[113px] top-0 absolute text-center text-[#894799] text-[40px] font-bold font-['Poppins']">
            More than 2K Lecturers use AutoGradePro From
          </div>
          <div className="w-[1194px] h-[102px] pl-5 pr-[19.09px] pt-[31px] pb-[21px] left-0 top-[60px] absolute justify-center items-start gap-[93.03px] inline-flex">
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-1.png"
              alt="Institution Logo 1"
              width={114}
              height={50}
            />
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-2.png"
              alt="Institution Logo 2"
              width={114}
              height={50}
            />
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-3.png"
              alt="Institution Logo 3"
              width={114}
              height={50}
            />
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-4.png"
              alt="Institution Logo 4"
              width={114}
              height={50}
            />
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-5.png"
              alt="Institution Logo 5"
              width={114}
              height={50}
            />
            <Image
              className="w-[114.28px] h-[50px] object-contain"
              src="/institutions/1-6.png"
              alt="Institution Logo 6"
              width={114}
              height={50}
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default Hero;
