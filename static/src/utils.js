export const isPrimitive = o => {
  return typeof o !== "object" || null;
};

export const isObject = o => {
  return !isPrimitive(o);
};

export const compareValues = (key, order = "asc") => {
  /**
   * function for dynamic sorting
   * Usage:
   * items.sort(compareValues('key'));
   * items.sort(compareValues('key', 'desc'));
   **/
  return function(a, b) {
    if (!a.hasOwnProperty(key) || !b.hasOwnProperty(key)) {
      // property doesn't exist on either object
      return 0;
    }

    const varA = typeof a[key] === "string" ? a[key].toUpperCase() : a[key];
    const varB = typeof b[key] === "string" ? b[key].toUpperCase() : b[key];

    let comparison = 0;
    if (varA > varB) {
      comparison = 1;
    } else if (varA < varB) {
      comparison = -1;
    }
    return order == "desc" ? comparison * -1 : comparison;
  };
};

export const orderBy = (items, key, order) => {
  if (order && order === "desc") {
    return items.sort(compareValues(key, "desc"));
  } else {
    return items.sort(compareValues(key));
  }
};

function buildFormData(formData, data, parentKey) {
  if (
    data &&
    typeof data === "object" &&
    !(data instanceof Date) &&
    !(data instanceof File)
  ) {
    Object.keys(data).forEach(key => {
      buildFormData(
        formData,
        data[key],
        parentKey ? `${parentKey}[${key}]` : key
      );
    });
  } else {
    const value = data == null ? "" : data;

    formData.append(parentKey, value);
  }
}

export const jsonToFormData = data => {
  const formData = new FormData();
  buildFormData(formData, data);
  return formData;
};

export const getRandomString = () => {
  return (
    Math.random()
      .toString(36)
      .substring(2, 15) +
    Math.random()
      .toString(36)
      .substring(2, 15)
  );
};
