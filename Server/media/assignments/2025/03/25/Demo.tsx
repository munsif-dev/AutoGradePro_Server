import React from "react";
import Image from "next/image";

const Demo = () => {
  return (
    <div className="w-full flex justify-center items-center p-10 ">
      <Image
        src="/VideoPlayer.png"
        alt="Video Player"
        width={900}
        height={300} // Use a correct aspect ratio or approximate height based on your image
        // This will automatically adjust the height based on the width
      />
    </div>
  );
};

export default Demo;
