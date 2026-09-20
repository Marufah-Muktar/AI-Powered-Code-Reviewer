const BASE_URL = "http://localhost:8000";

export const reviewCode = async (code, language) => {
  try {
    const response = await fetch(`${BASE_URL}/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code, language }),
    });

    if (!response.ok) {
      throw new Error("API failed");
    }

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    throw error;
  }
};