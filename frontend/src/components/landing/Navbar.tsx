import { Menu, X } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { label: "Features", id: "features" },
    { label: "How it Works", id: "how-it-works" },
    { label: "Technology", id: "technology" },
    { label: "Roadmap", id: "roadmap" },
  ];

  const scrollToSection = (id: string) => {
    const section = document.getElementById(id);

    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }

    setIsOpen(false);
  };

  const handleGenerateDNA = () => {
    const section = document.getElementById("generate-dna");

    if (section) {
      section.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }

    setIsOpen(false);
  };

  return (
    <motion.nav
      initial={{ y: -40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6 }}
      className="fixed left-0 right-0 top-0 z-50 border-b border-white/10 bg-[#09090B]/85 backdrop-blur-xl"
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-21">
     
        {/* BRAND */}
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="flex items-center"
        >
          <img
            src="/personadna-navbar-logo.png"
            alt="PersonaDNA"
            className="h-50  w-70 object-contain"
          />
        </button>

        {/* DESKTOP NAVIGATION */}
        <div className="hidden items-center gap-9 md:flex">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className="text-sm font-medium text-gray-300 transition hover:text-white"
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* DESKTOP CTA */}
        <div className="hidden md:block">
          <button
            onClick={handleGenerateDNA}
            className="rounded-xl bg-blue-600 px-21 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-500 hover:shadow-blue-500/30"
          >
            Generate DNA
          </button>
        </div>

        {/* MOBILE MENU BUTTON */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-white md:hidden"
          aria-label="Toggle navigation menu"
        >
          {isOpen ? <X size={26} /> : <Menu size={26} />}
        </button>
      </div>

      {/* MOBILE DRAWER */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="border-t border-white/10 bg-[#09090B] md:hidden"
        >
          <div className="flex flex-col gap-2 px-6 py-6">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="rounded-lg px-3 py-3 text-left text-gray-300 transition hover:bg-white/5 hover:text-white"
              >
                {item.label}
              </button>
            ))}

            <button
              onClick={handleGenerateDNA}
              className="mt-2 rounded-xl bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-500"
            >
              Generate DNA
            </button>
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
};

export default Navbar;
