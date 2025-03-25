import React from "react";
import Image from "next/image";

const InputAndLink = () => {
  return (
    <div className="w-full flex justify-center items-center mt-11 pt-6 bg-[#894799]">
      <div className="w-[1516px] h-[740px] relative">
        <div className="w-[1516px] h-[750px] left-0 top-0 absolute justify-center items-center inline-flex">
          <div className="grow shrink basis-0 self-stretch justify-center items-center inline-flex">
            <div className="w-[1516px] h-[935px] relative" />
          </div>
        </div>
        <div className="w-[1345px] h-[740px] left-[65px] top-[40px] absolute">
          <div className="w-[1128px] h-[380px] left-[137px] top-0 absolute">
            <div className="w-[425px] h-[199px] pl-8 pr-[2.19px] pb-px left-0 top-[66px] absolute flex-col justify-start items-start gap-[15px] inline-flex">
              <div className="w-[391px] h-[180px] text-center text-[#ffcece] text-xl font-medium font-['Poppins'] leading-[25px]">
                "Seamlessly grade answers from various input formats, including
                Word documents and text files. Our
                platform supports diverse file types to ensure all student
                submissions are accurately assessed."
              </div>
            </div>
            <Image
              alt="Generate Link"
              width={552}
              height={376}
              className="w-[552px]  left-[576px] top-0 absolute"
              src="/generateLink.png"
            />
          </div>
          <div className="w-[1345px] h-[377px] left-0 top-[300px] absolute">
            <div className="h-[151px] pl-8 pr-[2.19px] pb-px left-[744px] top-[113px] absolute flex-col justify-start items-start gap-[15px] inline-flex">
              <div className="w-[418px] text-center text-[#ffcece] text-xl font-medium font-['Poppins'] leading-[25px]">
                "Seamlessly grade answers from various input formats, including
                Word documents and text files. Our
                platform supports diverse file types to ensure all student
                submissions are accurately assessed."
              </div>
            </div>
            <Image
              width={684}
              height={377}
              alt="Student Upload"
              className="w-[684px]  left-0 top-0 absolute"
              src="/studentUpload.png"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default InputAndLink;

// Find and Match the same occurence in the code snippet below:
// using the short cut key -> Ctrl + Shift + L
