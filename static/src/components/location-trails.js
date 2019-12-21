import Vue from "@/vue";

import { orderBy } from "@/utils.js";

new Vue({
  el: "#location-trails",
  data: {
    headerNames: headerNames,
    trails: trails,
    sortBy: {
      key: "name",
      ascending: false
    }
  },
  mounted() {
    this.sortData("name");
  },
  methods: {
    sortData(sortKey) {
      this.$set(this.sortBy, "ascending", !this.sortBy.ascending);
      const method = this.sortBy.ascending ? "asc" : "desc";
      this.trails = orderBy(this.trails, sortKey, method);
      this.$set(this.sortBy, "key", sortKey);
    }
  }
});
