import exp from "constants";
import React from "react";
import Image from "next/image";
import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-white">
      <div className="mx-auto max-w-screen-xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="md:flex md:items-center md:gap-12">
            <Link
              className=" text-teal-600 flex  items-center justify-center"
              href="#"
            >
              <Image
                src="/Logo.png"
                alt="Logo"
                width={56} // corresponds to "w-14" in Tailwind (14 * 4 = 56)
                height={56} // corresponds to "h-14" in Tailwind (14 * 4 = 56)
              />
              <div className="w-auto  text-[#894799] text-lg font-extrabold font-['Montserrat']">
                AutoGradePro
              </div>
            </Link>
          </div>

          <div className="hidden md:block">
            <nav aria-label="Global">
              <ul className="flex items-center gap-6 text-sm">
                <li>
                  <Link
                    className="text-gray-500 transition hover:text-gray-500/75"
                    href="/dashboard"
                  >
                    Get Started
                  </Link>
                </li>

                <li>
                  <Link
                    className="text-gray-500 transition hover:text-gray-500/75"
                    href="#"
                  >
                    Services
                  </Link>
                </li>

                <li>
                  <Link
                    className="text-gray-500 transition hover:text-gray-500/75"
                    href="#"
                  >
                    Projects
                  </Link>
                </li>

                <li>
                  <Link
                    className="text-gray-500 transition hover:text-gray-500/75"
                    href="#"
                  >
                    Blog
                  </Link>
                </li>
              </ul>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="sm:flex sm:gap-4">
              <Link
                className="rounded-full bg-light-2 px-5 py-2.5 text-sm font-medium text-white shadow"
                href="/sign-in"
              >
                Login
              </Link>

              <div className="hidden sm:flex">
                <Link
                  className="rounded-full bg-gray-100 px-5 py-2.5 text-sm font-medium text-light-2"
                  href="/sign-up"
                >
                  Register
                </Link>
              </div>
            </div>

            <div className="block md:hidden">
              <button className="rounded bg-gray-100 p-2 text-gray-600 transition hover:text-gray-600/75">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="size-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
