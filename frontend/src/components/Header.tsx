export default function Header() {
  return (
    <header className="text-center py-8 border-b border-gray-200 dark:border-gray-700">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
        SynthID Tool
      </h1>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Detect and remove SynthID watermarks from AI-generated images
      </p>
    </header>
  );
}
