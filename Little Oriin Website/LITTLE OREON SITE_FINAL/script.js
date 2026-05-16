const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");

menuToggle?.addEventListener("click", () => {
  const isOpen = navLinks.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
});

navLinks?.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    menuToggle?.setAttribute("aria-expanded", "false");
  });
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.14 }
);

document.querySelectorAll("[data-reveal]").forEach((element) => observer.observe(element));

const programs = {
  academics: {
    kicker: "Foundation to future skills",
    title: "Academic mastery with digital confidence.",
    text:
      "Learners build literacy, numeracy, science thinking, communication, and problem solving through clear instruction and hands-on projects.",
    list: [
      "Interactive lessons and project-based assessments",
      "Reading, numeracy, coding logic, and science exploration",
      "Parent progress updates and learner growth goals",
    ],
  },
  talent: {
    kicker: "My talent",
    title: "A school day that makes space for gifts to emerge.",
    text:
      "Music, movement, art, sports, public speaking, and leadership are treated as serious parts of a learner's future.",
    list: [
      "Talent clubs and showcase events",
      "Creative studios for music, art, and performance",
      "Leadership roles that build courage and responsibility",
    ],
  },
  wellbeing: {
    kicker: "Whole-child growth",
    title: "Supportive systems for confidence, safety, and belonging.",
    text:
      "A warm school culture helps learners feel seen, organized, encouraged, and ready to take on new challenges.",
    list: [
      "Mentorship and values-based guidance",
      "Health, safety, and attendance communication",
      "Parent partnership around learner wellbeing",
    ],
  },
};

const tabs = document.querySelectorAll(".tab");
const kicker = document.querySelector("#program-kicker");
const title = document.querySelector("#program-title");
const text = document.querySelector("#program-text");
const list = document.querySelector("#program-list");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const program = programs[tab.dataset.tab];
    if (!program) return;

    tabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");

    kicker.textContent = program.kicker;
    title.textContent = program.title;
    text.textContent = program.text;
    list.innerHTML = program.list.map((item) => `<li>${item}</li>`).join("");
  });
});

document.querySelector(".contact-form")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button");
  const status = form.querySelector(".form-status");
  const formData = new FormData(form);
  formData.set("source", "Little Orion Eldoret website");
  const original = button.textContent;

  button.disabled = true;
  button.textContent = "Sending";
  if (status) {
    status.textContent = "";
  }

  fetch(form.action, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  })
    .then(async (response) => {
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        const errorMessage = data?.errors?.map((error) => error.message).join(" ") || "Unable to send inquiry";
        throw new Error(errorMessage);
      }
      form.reset();
      if (status) {
        status.textContent = "Successfully sent.";
      }
    })
    .catch((error) => {
      if (status) {
        status.textContent = error.message || "Could not send. Please try again.";
      }
    })
    .finally(() => {
      button.disabled = false;
      button.textContent = original;
    });

  setTimeout(() => {
    if (status) {
      status.textContent = "";
    }
  }, 6000);
});
