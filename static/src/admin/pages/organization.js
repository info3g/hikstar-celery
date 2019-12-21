import "@babel/polyfill";

import Vue from "@/vue.js";
import axios from "axios";

import { isObject } from "@/utils.js";

axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

new Vue({
  el: "#org-detail-component",
  data: {
    errors: {},
    isEditing: false,
    loading: false,

    // this should be the same with the org from db
    // used in resetting data
    savedOrg: {},

    organization: {
      address: {},
      user: {}
    }
  },
  mounted() {
    const textContent = document.getElementById("organization_data")
      .textContent;
    const org = JSON.parse(textContent)
    if (!org.address) {
      this.$set(org, "address", {})
    }
    this.savedOrg = {...org};
    this.organization = {...org};
  },
  computed: {
    formattedAddress() {
      const address = this.organization.address;
      const keys = ["province", "postal_code", "country"];
      const streetCity = [];
      const values = [];

      if (address.street_name) {
        streetCity.push(address.street_name.trim());
      }

      if (address.city) {
        streetCity.push(address.city.trim());
      }

      if (streetCity.length > 0) {
        values.push(streetCity.join(" "));
      }

      for (const key of keys) {
        const value = address[key];
        if (value) {
          values.push(value.trim());
        }
      }

      return values.join(", ");
    }
  },
  methods: {
    getError(key) {
      let error = this.errors;
      for (const k of key.split(".")) {
        error = error[k];
        if (!error) {
          return;
        }
      }
      if (Array.isArray(error)) {
        return error[0];
      }
      return error;
    },
    toggleEditing() {
      this.isEditing = !this.isEditing;
      this.errors = {};
    },
    cancel() {
      this.organization = JSON.parse(JSON.stringify(this.savedOrg));
      this.toggleEditing();
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    save() {
      this.loading = true;
      const url = `/api/organizations/${this.organization.id}/`;
      axios
        .patch(url, this.organization)
        .then(res => {
          this.savedOrg = JSON.parse(JSON.stringify(this.organization));
          $("li.breadcrumb-item")
            .last()
            .text(this.organization.name);
          this.toggleEditing();
          window.scrollTo({ top: 0, behavior: "smooth" });
        })
        .catch(error => {
          this.errors = error.response.data;
        })
        .finally(() => {
          this.loading = false;
        });
    }
  }
});
