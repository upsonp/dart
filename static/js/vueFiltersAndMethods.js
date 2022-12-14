function groomJSON(json) {
  return JSON.stringify(json).replaceAll("{", "").replaceAll("}", "").replaceAll("[", " ").replaceAll("]", " ").replaceAll('"', "").replaceAll("non_field_errors:", "")
}

vueFiltersObject = {
  floatformat: function (value, precision = 2) {
    if (!value) return '---';
    value = value.toLocaleString(undefined, {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    });
    return value
  },
  zero2NullMark: function (value) {
    if (!value || value === "0.00" || value == 0) return '---';
    return value
  },
  nz: function (value, arg = "---") {
    if (value === null || value === "") return arg;
    return value
  },
  yesNo: function (value) {
    if (value == null || value === false || value === 0) return 'No';
    return "Yes"
  },
  percentage: function (value, decimals) {
    // https://gist.github.com/belsrc/672b75d1f89a9a5c192c
    if (!value) value = 0;
    if (!decimals) decimals = 0;
    value = value * 100;
    value = Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
    value = value + '%';
    return value;
  },
  truncate: function (value, maxLength) {
    if (value && value.length > maxLength) return `${value.slice(0, maxLength)}...`
    return value
  }

  // truncate: function (value, max) {
  //   https://gist.github.com/belsrc/672b75d1f89a9a5c192c
  // if (!value) value = 0;
  // if (!decimals) decimals = 0;
  // value = value * 100;
  // value = Math.round(value * Math.pow(10, decimals)) / Math.pow(10, decimals);
  // value = value + '%';
  // return value;
  // }
}