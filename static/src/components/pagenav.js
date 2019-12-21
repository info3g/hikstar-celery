import "@babel/polyfill";
import Vue from "@/vue";

new Vue({
  el: "#pagenav-wrapper",
  data: {
    activeSection: null,
    sections: []
  },
  mounted() {
    $("#loading-mask").fadeOut();
    $("body").removeClass("no-scroll");
    const vm = this;
    $(document).ready(function() {
      vm.sections = [...document.querySelectorAll("section")];
    });
    document.addEventListener("scroll", this.onScroll);
  },
  computed: {
    navItems() {
      const items = [];
      for (const element of this.sections) {
        if (element.dataset.pagenavName) {
          items.push({
            id: element.id,
            title: element.dataset.pagenavName
          });
        }
      }
      return items;
    }
  },
  methods: {
    scrollTo(sectionId) {
      this.activeSection = sectionId;
      const y = document.getElementById(sectionId).offsetTop - 50;
      window.scrollTo(0, y);
    },
    onScroll() {
      const top = document.documentElement.scrollTop || document.body.scrollTop;
      const topDistance = $("#pagenav-wrapper").offset().top;

      if (topDistance > top) {
        $("#pagenav-wrapper div.pagenav").removeClass("Sticky");
      } else {
        $("#pagenav-wrapper div.pagenav").addClass("Sticky");
      }
      this.setActiveSection();
    },
    setActiveSection() {
      this.sections.map(section => {
        // scroll position
        const scrollPosition = section.scrollTop;

        const elmtToTop = section.getBoundingClientRect()["top"];

        const elmtHeight = section.offsetHeight;

        if (
          elmtToTop <= scrollPosition + 50 &&
          elmtToTop + elmtHeight > scrollPosition
        ) {
          this.activeSection = section.id;
        }
      });
    }
  }
});
