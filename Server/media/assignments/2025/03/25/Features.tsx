"use client";
import React from "react";
import AnimatedText from "./AnimatedText";
import Image from "next/image";

const Features = () => {
  return (
    <>
      <div className="w-full flex justify-center items-center mt-10 pt-11 ">
        <div className="w-[1181px] h-[135.12px] relative">
          <div className="w-[461px] h-[86.87px] left-[445px] top-[27.02px] absolute text-[#da7fc6] text-lg font-medium font-['Poppins'] capitalize leading-[30px]">
            We offer a variety of interesting features that you can help
            increase yor productivity when you are Grading your examinations
          </div>
          <div className="w-[408px] h-[135.12px] left-0 top-0 absolute text-[#894799] text-[40px] font-normal font-['Pacifico']">
            What AutoGradePro Offers!
          </div>
          <div className="w-[162px] h-[63.70px] left-[1019px] top-[38.61px] absolute">
            <div className="w-[162px] h-[63.70px] left-0 top-0 absolute bg-[#894799] rounded-[70px]" />
            <div className="w-[71px] h-[28.96px] left-[45px] top-[17.37px] absolute text-white text-lg font-medium font-['Poppins'] leading-[30px]">
              Try Free
            </div>
          </div>
        </div>
      </div>

      <div className="w-full flex justify-center items-center mt-5 pt-3 gap-12">
        <div className="w-[364px] h-[665.97px] relative">
          <img
            className="w-[364px] h-[415.02px]"
            src="scan_submission.png"
          ></img>
          <div className="w-[340px] h-[221.99px] left-0 top-[443.98px] absolute">
            <div className="w-[340px] h-[173.73px] left-0 top-[48.26px] absolute text-[#da7fc6] text-lg font-medium font-['Poppins'] leading-[30px]">
              Lecturers can upload bulk answers in any format.
              <br />
              Students can Scan the answers and Submit them through the link
              provided by Lecturers{" "}
            </div>
            <div className="w-[313px] h-[28.96px] left-0 top-0 absolute text-[#da7fc6] text-3xl font-semibold font-['Poppins'] leading-[30px]">
              Scan & Submission
            </div>
          </div>
        </div>
        <div className="w-[364px] h-[665.97px] relative">
          <Image
            className="w-[364px] h-[415.02px] object-cover"
            src="/grade_review.png"
            alt="Grade & Review"
            width={364}
            height={415}
          />
          <div className="w-[340px] h-[221.99px] left-0 top-[443.98px] absolute">
            <div className="w-[340px] h-[173.73px] left-0 top-[48.26px] absolute text-[#da7fc6] text-lg font-medium font-['Poppins'] leading-[30px]">
              Lecturers can effortlessly grade the answers by providing original answers to the system.
              <br />
              Students can review their gradings{" "}
            </div>
            <div className="w-[313px] h-[28.96px] left-0 top-0 absolute text-[#da7fc6] text-3xl font-semibold font-['Poppins'] leading-[30px]">
              Grade & Review
            </div>
          </div>
        </div>
        <div className="w-[364px] h-[665.97px] relative">
          <Image
            className="w-[364px] h-[415.02px] object-cover"
            src="/analytics_files.png"
            alt="Analytics & Files"
            width={364}
            height={415}
          />
          <div className="w-[340px] h-[221.99px] left-0 top-[443.98px] absolute">
            <div className="w-[340px] h-[173.73px] left-0 top-[48.26px] absolute text-[#da7fc6] text-lg font-medium font-['Poppins'] leading-[30px]">
              Lecturer can analyses the result in graphs.
              <br />
              lecturers can generate files of the analytics, and results{" "}
            </div>
            <div className="w-[313px] h-[28.96px] left-0 top-0 absolute text-[#da7fc6] text-3xl font-semibold font-['Poppins'] leading-[30px]">
              Analytics & Files
            </div>
          </div>
        </div>
      </div>
      <div className="w-full flex justify-center items-center mt-10 pb-3 pt-10 gap-12">
        <div className="w-[1151px] h-[500px] relative">
          <div className="w-[598px] left-0 top-[5px] absolute">
            <span className="text-[#da7fc6] text-2xl font-medium  leading-normal">
              Input Formats
              <br />
            </span>
            <span className="text-[#894799] text-3xl font-medium  capitalize leading-[41px]">
              mark answers from various formats like Word, and text files.
            </span>
          </div>

          <div className="h-[166px] pl-8 pr-[2.19px] pb-px mb-5 left-0 top-[168px] absolute flex-col justify-start items-start gap-[15px] inline-flex">
            <AnimatedText
              type="p"
              text={`"Seamlessly grade answers from various input formats, including Word documents and text files. Our platform supports diverse file types to ensure all student submissions are accurately assessed."`}
              className="w-[512px] text-[#696969] text-base font-medium font-['Poppins'] leading-[25px]"
            />

            <div className="w-[528px] text-[#696969] text-base font-medium font-['Poppins'] leading-[25px]">
              "An integrated support feature allows educators to get instant
              assistance, ensuring smooth and accurate grading every time!"
            </div>
          </div>
          <div className="pl-[47.81px] pr-[47.19px] pt-3.5 pb-4 left-0 top-[369px] absolute bg-[#894799] rounded-[70px] justify-start items-start inline-flex">
            <div className="text-center text-white text-[15px] font-normal font-['Poppins'] leading-tight">
              View A Demo
            </div>
          </div>
          <img
            className="w-[477px] h-[477px] left-[674px] top-0 absolute"
            src="inputFormats.png"
          />
        </div>
      </div>
    </>
  );
};

export default Features;
